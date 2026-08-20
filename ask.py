"""CLI for the portfolio RAG bot.

Usage:
    python ask.py <docs_folder>              # index if needed, then ask
    python ask.py <docs_folder> --reindex    # force re-embedding (docs changed)
"""
import os
import sys

from rag_core import build_index, answer, INDEX_PATH


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    folder = args[0] if args else "docs"
    reindex = "--reindex" in sys.argv

    if reindex or not os.path.exists(INDEX_PATH):
        count = build_index(folder)
        print(f"Indexed {count} chunks from '{folder}'.\n")
    else:
        print(f"Using cached index ({INDEX_PATH}). Pass --reindex if docs changed.\n")

    print("Ask a question about the portfolio (empty line or Ctrl+C to quit).")
    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not question:
            break
        text, sources = answer(question)
        print(f"\n{text}")
        print(f"\n  ↳ sources: {', '.join(sources)}")


if __name__ == "__main__":
    main()
