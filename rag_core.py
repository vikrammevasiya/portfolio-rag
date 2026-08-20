"""Portfolio RAG — reusable core: load, chunk, embed, retrieve, answer.

Used by the CLI (ask.py) and, later, a FastAPI endpoint. Keeping all the
logic here means the interface layers stay thin — the same pattern you used
with EmployeeManager.
"""
import sys
from pathlib import Path

import numpy as np
from google import genai

client = genai.Client()                 # reads GEMINI_API_KEY from the environment
EMBED_MODEL = "gemini-embedding-2"
CHAT_MODEL = "gemini-3.5-flash-lite"
INDEX_PATH = "portfolio_index.npz"

# Who the assistant is. Third-person, recruiter-friendly, grounded in the docs.
SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about Vikram, a software "
    "developer, for recruiters and visitors to his portfolio. Answer in the "
    "third person (e.g. 'Vikram has...'). Use ONLY the context provided. If the "
    "answer is not in the context, say you don't have that information rather "
    "than guessing. Be concise, warm, and professional."
)


# ---------------------------------------------------------------- loading ----
def read_pdf(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def load_documents(folder: str) -> list[dict]:
    """Read every .txt / .md / .pdf under `folder` into {source, text} dicts."""
    docs = []
    for path in sorted(Path(folder).rglob("*")):
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
        elif suffix == ".pdf":
            text = read_pdf(path)
        else:
            continue
        if text.strip():
            docs.append({"source": path.name, "text": text.strip()})
    return docs


# --------------------------------------------------------------- chunking ----
def chunk_text(text: str, max_words: int = 180, overlap: int = 40) -> list[str]:
    """Structure-aware chunking: pack paragraphs together up to max_words,
    carrying a small word overlap so ideas that straddle a boundary survive."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current: list[str] = []

    for para in paragraphs:
        words = para.split()
        if len(current) + len(words) > max_words and current:
            chunks.append(" ".join(current))
            current = current[-overlap:]          # overlap tail into next chunk
        current.extend(words)

    if current:
        chunks.append(" ".join(current))
    return chunks


# -------------------------------------------------------------- embedding ----
def embed(texts: list[str]) -> np.ndarray:
    """Embed each text individually -> one vector per text (matrix out)."""
    vectors = []
    for t in texts:
        result = client.models.embed_content(model=EMBED_MODEL, contents=t)
        vectors.append(result.embeddings[0].values)
    return np.array(vectors)


# ---------------------------------------------------------------- indexing ----
def build_index(folder: str, index_path: str = INDEX_PATH) -> int:
    """Load -> chunk -> embed -> save to disk. Returns number of chunks."""
    docs = load_documents(folder)
    if not docs:
        raise SystemExit(f"No .txt/.md/.pdf documents found in '{folder}'.")

    chunks, sources = [], []
    for d in docs:
        for c in chunk_text(d["text"]):
            chunks.append(c)
            sources.append(d["source"])

    print(f"Embedding {len(chunks)} chunks from {len(docs)} documents...", file=sys.stderr)
    vectors = embed(chunks)
    assert vectors.shape[0] == len(chunks), "vector count must match chunk count!"

    np.savez(
        index_path,
        vectors=vectors,
        chunks=np.array(chunks, dtype=object),
        sources=np.array(sources, dtype=object),
    )
    return len(chunks)


def load_index(index_path: str = INDEX_PATH):
    data = np.load(index_path, allow_pickle=True)
    return data["vectors"], list(data["chunks"]), list(data["sources"])


# --------------------------------------------------------------- retrieval ----
def cosine(q: np.ndarray, mat: np.ndarray) -> np.ndarray:
    return (mat @ q) / (np.linalg.norm(mat, axis=1) * np.linalg.norm(q))


def retrieve(question: str, k: int = 4):
    vectors, chunks, sources = load_index()
    q_vec = embed([question])[0]
    scores = cosine(q_vec, vectors)
    top = np.argsort(scores)[::-1][:k]
    return [(chunks[i], sources[i], float(scores[i])) for i in top]


def answer(question: str, k: int = 4):
    """Retrieve relevant chunks, ground the model on them, return (text, sources)."""
    hits = retrieve(question, k)
    context = "\n\n".join(f"[from {src}] {chunk}" for chunk, src, _ in hits)
    prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion: {question}"
    resp = client.models.generate_content(model=CHAT_MODEL, contents=prompt)
    used_sources = sorted({src for _, src, _ in hits})
    return resp.text, used_sources
