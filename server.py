"""FastAPI backend for the portfolio chatbot.

A thin web layer over rag_core — the same pattern as api.py over your
EmployeeManager. Your website's own server (never the browser directly)
calls POST /ask; this retrieves + answers.

IMPORTANT — how access control actually works here:
CORS only restricts BROWSERS. Tools like Postman/curl ignore it entirely.
So the real gate is the X-Api-Secret header, checked below. For that secret
to stay secret, the BROWSER must never see it — which means your frontend
must call your OWN server (a Next.js API route), and that server calls this
one, attaching the secret itself. See next_api_route/route.js.

Run locally:
    set -x GEMINI_API_KEY <your-key>
    set -x DOCS_FOLDER docs
    set -x ALLOWED_ORIGINS http://localhost:3000
    set -x API_SECRET some-long-random-string
    uvicorn server:app --reload
"""
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import rag_core

DOCS_FOLDER = os.environ.get("DOCS_FOLDER", "docs")
# Comma-separated list of origins allowed by CORS. With the secret-header
# gate in place this is now a secondary defense (it still stops a browser
# on another site from reading this API's response), not the main one.
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000"
).split(",")

# The real gate: a shared secret only your own backend/server knows.
# Never prefix this with NEXT_PUBLIC_ in your Next.js env — that prefix is
# what makes a variable visible to the browser bundle.
API_SECRET = os.environ.get("API_SECRET")

# Interactive docs are OFF by default — they make it trivial for anyone who
# finds the URL to explore and call every endpoint. Turn on locally only.
ENABLE_DOCS = os.environ.get("ENABLE_DOCS", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts: build the index if it doesn't exist yet.
    if not os.path.exists(rag_core.INDEX_PATH):
        rag_core.build_index(DOCS_FOLDER)
    yield


app = FastAPI(
    title="Portfolio Assistant API",
    lifespan=lifespan,
    docs_url="/docs" if ENABLE_DOCS else None,
    redoc_url="/redoc" if ENABLE_DOCS else None,
    openapi_url="/openapi.json" if ENABLE_DOCS else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class AskIn(BaseModel):
    question: str


def verify_secret(x_api_secret: str | None = Header(default=None)):
    """Dependency: reject any request that doesn't carry the shared secret.

    secrets.compare_digest avoids a "timing attack" — a naive `==` comparison
    returns slightly faster the sooner two strings differ, which an attacker
    can measure over many requests to guess the secret character by character.
    compare_digest always takes the same time regardless of where they differ.
    """
    if not API_SECRET:
        # Fail SAFE: if nobody configured a secret, refuse every request
        # rather than silently running wide open.
        raise HTTPException(status_code=503, detail="Server not configured.")
    if not x_api_secret or not secrets.compare_digest(x_api_secret, API_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized.")


@app.get("/health")
def health():
    # Deliberately unauthenticated — hosting platforms ping this to check
    # the app is alive. It reveals nothing about your data or docs.
    return {"status": "ok"}


@app.post("/ask", dependencies=[Depends(verify_secret)])
def ask(payload: AskIn):
    question = payload.question.strip()

    # Basic guardrails for a public-facing endpoint.
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question is too long.")

    answer_text, sources = rag_core.answer(question)
    return {"answer": answer_text}
