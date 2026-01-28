#!/usr/bin/env python3
"""
One-time script to generate justifications for all existing opportunities.

Usage (from repo root):
    cd backend
    python -m scripts.generate_all_justifications [--client-id <uuid>]

If no client-id provided, generates for ALL opportunities across all clients.
"""

import asyncio
import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from database import get_supabase
from services.project_justification import generate_opportunity_justifications


async def generate_all(client_id: str = None):
    """Generate justifications for all opportunities."""
    supabase = get_supabase()

    # Get opportunities
    query = supabase.table("ai_opportunities").select("id, title, client_id, opportunity_summary")

    if client_id:
        query = query.eq("client_id", client_id)

    result = query.execute()
    opportunities = result.data

    if not opportunities:
        print("No opportunities found.")
        return

    # Filter to only those without justifications
    needs_generation = [o for o in opportunities if not o.get("opportunity_summary")]

    print(f"Found {len(opportunities)} total opportunities")
    print(f"  - {len(needs_generation)} need justifications")
    print(f"  - {len(opportunities) - len(needs_generation)} already have justifications")
    print()

    if not needs_generation:
        print("All opportunities already have justifications!")
        return

    # Generate for each
    success = 0
    failed = 0

    for i, opp in enumerate(needs_generation, 1):
        print(f"[{i}/{len(needs_generation)}] Generating for: {opp['title'][:50]}...")
        try:
            await generate_opportunity_justifications(
                opportunity_id=opp["id"],
                client_id=opp["client_id"]
            )
            success += 1
            print(f"  ✓ Done")
        except Exception as e:
            failed += 1
            print(f"  ✗ Failed: {e}")

    print()
    print(f"Complete! Success: {success}, Failed: {failed}")


def main():
    parser = argparse.ArgumentParser(description="Generate justifications for all opportunities")
    parser.add_argument("--client-id", help="Limit to specific client UUID")
    parser.add_argument("--all", action="store_true", help="Regenerate ALL, even those with existing justifications")
    args = parser.parse_args()

    asyncio.run(generate_all(client_id=args.client_id))


if __name__ == "__main__":
    main()
