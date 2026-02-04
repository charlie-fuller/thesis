#!/usr/bin/env python3
"""Query PuRDy outputs from the last 24 hours for evaluation."""

import os
import sys
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from database import get_supabase


def main():
    supabase = get_supabase()

    # Calculate 24 hours ago
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    # Query outputs from last 24 hours
    result = (
        supabase.table("disco_outputs")
        .select(
            "id, agent_type, version, created_at, content_markdown, recommendation, confidence_level, tier_routing, initiative_id"
        )
        .gte("created_at", since)
        .order("agent_type")
        .order("created_at", desc=True)
        .execute()
    )

    if not result.data:
        print("No outputs found in the last 24 hours.")
        print("\nLet me check recent outputs without time filter...")

        # Get recent outputs without time filter
        result = (
            supabase.table("disco_outputs")
            .select(
                "id, agent_type, version, created_at, content_markdown, recommendation, confidence_level, tier_routing, initiative_id"
            )
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )

    # Get initiative names
    initiative_ids = list({o.get("initiative_id") for o in result.data if o.get("initiative_id")})
    initiatives = {}
    if initiative_ids:
        init_result = supabase.table("disco_initiatives").select("id, name").in_("id", initiative_ids).execute()
        initiatives = {i["id"]: i["name"] for i in (init_result.data or [])}

    print(f"\n{'=' * 80}")
    print("PURDY OUTPUTS FOR EVALUATION")
    print(f"{'=' * 80}\n")

    # Group by agent type
    by_agent = {}
    for output in result.data:
        agent_type = output.get("agent_type", "unknown")
        if agent_type not in by_agent:
            by_agent[agent_type] = []
        by_agent[agent_type].append(output)

    for agent_type, outputs in sorted(by_agent.items()):
        print(f"\n{'=' * 80}")
        print(f"AGENT: {agent_type.upper()}")
        print(f"Total outputs: {len(outputs)}")
        print(f"{'=' * 80}")

        for _i, output in enumerate(outputs[:4], 1):  # Last 4 versions
            init_name = initiatives.get(output.get("initiative_id"), "Unknown")
            print(f"\n--- Version {output.get('version')} | Initiative: {init_name} ---")
            print(f"Created: {output.get('created_at')}")
            print(f"Recommendation: {output.get('recommendation')}")
            print(f"Confidence: {output.get('confidence_level')}")
            print(f"Tier Routing: {output.get('tier_routing')}")
            print(f"Content length: {len(output.get('content_markdown', ''))} chars")
            print("\n--- CONTENT PREVIEW (first 3000 chars) ---")
            content = output.get("content_markdown", "")[:3000]
            print(content)
            print(f"\n{'=' * 40}")

    print(f"\n\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total outputs: {len(result.data)}")
    for agent_type, outputs in sorted(by_agent.items()):
        print(f"  {agent_type}: {len(outputs)} outputs")


if __name__ == "__main__":
    main()
