from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Allow: python scripts/platypus_read_proof.py ...
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.platypus import PlatypusClient, PlatypusError  # noqa: E402


async def main() -> int:
    parser = argparse.ArgumentParser(description="Sprint 4.4.0a Platypus read proof")
    parser.add_argument("search", nargs="?", help="Customer name, phone, ID, or username. Omit when using --customer-id.")
    parser.add_argument("--customer-id", help="Explicit Platypus customer ID")
    args = parser.parse_args()

    if not args.search and not args.customer_id:
        parser.error("provide a customer search or --customer-id")

    client = PlatypusClient()
    try:
        if args.customer_id:
            proof = await client.read_customer_proof(args.customer_id)
        else:
            proof = {"search": await client.search_customers(args.search or "")}
    except PlatypusError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(proof, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
