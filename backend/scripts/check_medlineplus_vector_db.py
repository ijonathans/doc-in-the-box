"""
Check that the MedlinePlus collection exists in Actian Vector DB and has data.

Usage (from backend directory):
    set PYTHONPATH=.
    python -m scripts.check_medlineplus_vector_db

Environment: ACTIAN_HOST (default localhost:50051). Optional: OPENAI_API_KEY for a sample search.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.services.kb_medlineplus_service import KBMedlinePlusService


async def main() -> None:
    kb = KBMedlinePlusService()
    if not kb.is_available:
        print("FAIL: Actian Cortex client not available (install actiancortex).")
        sys.exit(1)

    print(f"Connecting to Actian at {kb.host}...")
    try:
        from cortex import AsyncCortexClient
    except ImportError:
        print("FAIL: cortex module not found.")
        sys.exit(1)

    async with AsyncCortexClient(kb.host) as client:
        # 1. Collection exists?
        exists = await client.has_collection(kb.collection)
        if not exists:
            print(f"FAIL: Collection '{kb.collection}' does not exist. Run the ingest script first.")
            sys.exit(1)
        print(f"OK: Collection '{kb.collection}' exists.")

        # 2. Vector count
        count = await client.count(kb.collection)
        print(f"OK: Vector count = {count}")

        # 3. Optional: one search (needs OPENAI_API_KEY)
        if count > 0:
            results = await kb.search("headache", top_k=2)
            if results:
                print("OK: Sample search for 'headache' returned results:")
                for i, r in enumerate(results, 1):
                    print(f"   {i}. {r.get('title', 'N/A')} (score: {r.get('score', 0):.4f})")
            else:
                print("Note: Sample search returned no results (OPENAI_API_KEY may be unset or embedding failed).")

    print("\nVector AI DB check completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
