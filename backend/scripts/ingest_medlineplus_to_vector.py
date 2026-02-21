"""
Ingest MedlinePlus topics CSV into Actian Vector DB.

Reads the CSV, strips HTML from full-summary, builds one vector per row (title + meta-desc + plain summary),
embeds with OpenAI, and batch_upserts into the medlineplus_topics collection.

Usage (from backend directory):
    set PYTHONPATH=.
    python -m scripts.ingest_medlineplus_to_vector [path_to_csv]

Environment: OPENAI_API_KEY, ACTIAN_HOST (default localhost:50051).
Default CSV path: repo_root/actian-vectorAI-db-beta/documents/medlineplus_topics_english_2025-11-19.csv
"""

import argparse
import asyncio
import csv
import re
import sys
from pathlib import Path

# Run from backend; ensure app is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.services.kb_medlineplus_service import KBMedlinePlusService
from app.services.memory.embedding_service import EmbeddingService

BATCH_SIZE = 200
DEFAULT_CSV_NAME = "medlineplus_topics_english_2025-11-19.csv"


def _default_csv_path() -> Path:
    repo_root = Path(__file__).resolve().parent.parent.parent
    return repo_root / "actian-vectorAI-db-beta" / "documents" / DEFAULT_CSV_NAME


def _strip_html(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _build_row_text(row: dict) -> str:
    title = (row.get("title") or "").strip()
    meta = (row.get("meta-desc") or "").strip()
    summary = _strip_html(row.get("full-summary") or "")
    return f"{title} {meta} {summary}".strip()


def _to_int_id(index: int) -> int:
    """Stable unique int for Actian (one vector per row)."""
    return index % (10**9)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest MedlinePlus CSV into Actian Vector DB")
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=_default_csv_path(),
        help="Path to MedlinePlus CSV (default: repo actian-vectorAI-db-beta/documents/...)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="If set, only ingest this many rows (for testing). 0 = all rows.",
    )
    args = parser.parse_args()
    csv_path: Path = args.csv_path
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        sys.exit(1)

    kb = KBMedlinePlusService()
    embedding = EmbeddingService()
    if not kb.is_available:
        print("Actian Cortex client not available (install actiancortex).")
        sys.exit(1)

    print(f"Ensuring collection '{kb.collection}'...")
    await kb.ensure_collection()

    rows: list[dict] = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            if args.limit and len(rows) >= args.limit:
                break

    total = len(rows)
    print(f"Loaded {total} rows. Embedding and upserting in batches of {BATCH_SIZE}...")

    for start in range(0, total, BATCH_SIZE):
        batch = rows[start : start + BATCH_SIZE]
        texts = [_build_row_text(r) for r in batch]
        ids = [_to_int_id(start + i) for i in range(len(batch))]
        vectors = [await embedding.embed_text(t) for t in texts]
        payloads = [
            {
                "id": r.get("id"),
                "title": (r.get("title") or "").strip(),
                "url": (r.get("url") or "").strip(),
                "text": texts[i],
                "groups": (r.get("groups") or "").strip()[:500],
            }
            for i, r in enumerate(batch)
        ]
        await kb.batch_upsert(ids, vectors, payloads)
        print(f"  Upserted {start + len(batch)} / {total}")

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
