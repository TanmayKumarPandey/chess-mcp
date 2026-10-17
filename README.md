# Chess helper MCP server

Gives Claude two tools backed by Stockfish: `best_move` and `position_fen`.

## 1. Deploy (needs a public https URL)
Put these 4 files in a GitHub repo, then create a **Docker web service**
on a host such as Render, Railway or Fly.io pointing at that repo.
The Dockerfile installs Stockfish for you. The server listens on `$PORT`
(default 8000) and serves MCP at the `/mcp` path, so your connector URL is
**`https://YOUR-APP-URL/mcp`**.

Test locally first:

    docker build -t chess-mcp .
    docker run -p 8000:8000 chess-mcp
    # MCP endpoint: http://localhost:8000/mcp

## 2. Connect to Claude
Settings -> Connectors -> add custom connector -> paste `https://YOUR-APP-URL/mcp`.
(Menu names and availability may vary by plan and device.)

## 3. Use it
Ask: "Use best_move with these moves: 1. e4 e5 2. Nf3 Nc6 ..."

## Notes
- No login: anyone with the URL can use it. It only computes chess moves,
  and time per call is capped at 10 s, but keep the URL private.
- Free hosting tiers may sleep; the first call can be slow.
