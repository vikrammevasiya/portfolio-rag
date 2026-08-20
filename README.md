# Portfolio Assistant — Backend

A FastAPI + RAG backend that answers questions about Vikram's portfolio,
grounded in the documents in `docs/`. Deployed separately from the portfolio
website itself; the React widget (`PortfolioChat.jsx`) calls this API.

## Files

- `rag_core.py` — loading, chunking, embedding, retrieval, and answering.
- `server.py` — the FastAPI web layer (routes, CORS, validation).
- `ask.py` — a local CLI for testing retrieval without the web layer.
- `docs/` — your portfolio source documents (.txt / .md / .pdf).
- `portfolio_index.npz` — the prebuilt embedding index (committed so Railway
  doesn't need to re-embed on every deploy; rebuild locally when docs change).
- `requirements.txt`, `Procfile` — deployment config for Railway.

## Environment variables (set these on Railway, never commit them)

| Variable | Example | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | `AIza...` | Your Gemini API key |
| `DOCS_FOLDER` | `docs` | Folder the index is built from |
| `ALLOWED_ORIGINS` | `https://your-portfolio.com` | CORS allow-list, comma-separated |

## Local development

```bash
python -m venv .venv
source .venv/bin/activate       # fish: source .venv/bin/activate.fish
pip install -r requirements.txt
export GEMINI_API_KEY=your-key  # fish: set -x GEMINI_API_KEY your-key
export DOCS_FOLDER=docs
export ALLOWED_ORIGINS=http://localhost:3000
uvicorn server:app --reload
```

## Rebuilding the index after editing docs/

```bash
python ask.py docs --reindex
```

This regenerates `portfolio_index.npz`. Commit and push it so the deployed
backend picks up the change (or re-run the same command from a shell on the
deployed host, if you'd rather not commit the binary index).

## Deploying to Railway

See the deployment walkthrough — push this repo to GitHub, then on
[railway.app](https://railway.app): New Project → Deploy from GitHub repo →
select this repo → set the three environment variables above in the
Variables tab → Railway builds and deploys automatically using `Procfile`.
Railway assigns a public URL like `https://<name>.up.railway.app`; point the
React widget's `apiUrl` prop at it.
