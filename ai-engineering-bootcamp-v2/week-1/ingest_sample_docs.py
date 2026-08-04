"""Ingest every .txt file in week-2/sample_docs/ into the vector store via POST /ingest.

Run:
  python ingest_sample_docs.py [base_url]

base_url defaults to http://127.0.0.1:8000.
"""

import sys
from pathlib import Path

import httpx

SAMPLE_DOCS_DIR = Path(__file__).resolve().parent.parent / "week-2" / "sample_docs"


def main() -> None:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    base_url = base_url.rstrip("/")

    files = sorted(SAMPLE_DOCS_DIR.glob("*.txt"))
    if not files:
        print(f"No .txt files found in {SAMPLE_DOCS_DIR}")
        return

    with httpx.Client(timeout=60.0) as client:
        for path in files:
            text = path.read_text(encoding="utf-8")
            document_id = path.stem  # stable id derived from filename, e.g. netflix_culture_memo

            response = client.post(
                f"{base_url}/ingest",
                json={
                    "document_id": document_id,
                    "text": text,
                    "metadata": {"source": path.name},
                },
            )
            response.raise_for_status()
            data = response.json()
            print(f"{path.name} -> document_id={document_id} chunks_indexed={data['chunks_indexed']}")

        stats = client.get(f"{base_url}/debug/pinecone")
        stats.raise_for_status()
        print(f"Total vectors in store: {stats.json()['total_vector_count']}")


if __name__ == "__main__":
    main()
