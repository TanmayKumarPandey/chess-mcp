"""Chess helper MCP server: lets Claude ask Stockfish for the best move."""
import os
import re

import chess
import chess.engine
from mcp.server.fastmcp import FastMCP

STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH", "/usr/games/stockfish")
MAX_SECONDS = 10.0  # cap so nobody can tie up the server
MAX_LINES = 5

mcp = FastMCP(
    "chess-helper",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8000")),
)


def build_board(fen: str, moves: str) -> chess.Board:
    """Start from a FEN (or the standard start) and replay SAN moves."""
    board = chess.Board(fen.strip()) if fen.strip() else chess.Board()
    text = moves.replace("0-0-0", "O-O-O").replace("0-0", "O-O")
    text = re.sub(r"\d+\.(\.\.)?", " ", text)  # drop "1." and "1..."
    for token in text.split():
        if token in ("1-0", "0-1", "1/2-1/2", "*"):
            continue
        try:
            board.push_san(token)
        except ValueError:
            raise ValueError(
                f"Illegal or unreadable move '{token}' in position {board.fen()}"
            )
    return board


def fmt_score(score: chess.engine.PovScore, turn: bool) -> str:
    s = score.pov(turn)
    if s.is_mate():
        return f"mate in {abs(s.mate())} ({'for' if s.mate() > 0 else 'against'} side to move)"
    return f"{s.score() / 100:+.2f}"


@mcp.tool()
def best_move(moves: str = "", fen: str = "", seconds: float = 2.0, lines: int = 3) -> str:
    """Ask Stockfish for the best move.

    Give either `moves` (SAN from the start, e.g. "1. e4 e5 2. Nf3 Nc6")
    or `fen` (optionally with `moves` played after it).
    Scores are from the side to move's point of view (+ is good for them).
    """
    board = build_board(fen, moves)
    if board.is_game_over():
        return f"Game is over: {board.result()} ({board.outcome().termination.name})"

    seconds = max(0.1, min(float(seconds), MAX_SECONDS))
    lines = max(1, min(int(lines), MAX_LINES))
    side = "White" if board.turn == chess.WHITE else "Black"

    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
        infos = engine.analyse(board, chess.engine.Limit(time=seconds), multipv=lines)

    out = [f"{side} to move. FEN: {board.fen()}"]
    for i, info in enumerate(infos, 1):
        pv = info["pv"][:6]
        out.append(
            f"{i}. {board.san(pv[0])} (eval {fmt_score(info['score'], board.turn)}) "
            f"line: {board.variation_san(pv)}"
        )
    return "\n".join(out)


@mcp.tool()
def position_fen(moves: str, fen: str = "") -> str:
    """Replay moves and return the FEN, side to move, and any check/game-over status."""
    board = build_board(fen, moves)
    status = []
    if board.is_check():
        status.append("check")
    if board.is_game_over():
        status.append(f"game over {board.result()}")
    return (
        f"FEN: {board.fen()}\n"
        f"Side to move: {'White' if board.turn else 'Black'}\n"
        f"Status: {', '.join(status) or 'normal'}"
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")  # served at /mcp
