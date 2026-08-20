"""FastAPI backend for the portfolio chatbot.

A thin web layer over rag_core — the same pattern as api.py over your
EmployeeManager. Your React site calls POST /ask; this retrieves + answers.

Run locally:
    set -x GEMINI_API_KEY <your-key>
    set -x DOCS_FOLDER docs
    set -x ALLOWED_ORIGINS http://localhost:3000
    uvicorn server:app --reload
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import rag_core

DOCS_FOLDER = os.environ.get("DOCS_FOLDER", "docs")
# Comma-separated list of sites allowed to call this API from a browser.
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000"
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts: build the index if it doesn't exist yet.
    if not os.path.exists(rag_core.INDEX_PATH):
        rag_core.build_index(DOCS_FOLDER)
    yield


app = FastAPI(title="Portfolio Assistant API", lifespan=lifespan)

# CORS middleware — this is the app-wide "middleware" concept from the auth
# lesson. Without it, browsers block your website from calling this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class AskIn(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(payload: AskIn):
    question = payload.question.strip()

    # Basic guardrails for a public endpoint.
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question is too long.")

    answer_text, sources = rag_core.answer(question)
    return {"answer": answer_text, "sources": sources}
