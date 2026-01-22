#!/usr/bin/env python3
"""
Evaluate confidence scores for all opportunities.

Usage:
    cd backend
    uv run python scripts/evaluate_opportunity_confidence.py

This script:
1. Fetches all opportunities from the database
2. Evaluates confidence based on the rubric (information completeness)
3. Generates questions that would raise confidence
4. Updates each opportunity with scoring_confidence and confidence_questions

Rubric (100 points max):
- All 4 dimension scores: +20
- Has description: +10
- Has current_state: +8
- Has desired_state: +8
- Has owner: +12
- Has department: +5
- Has ROI indicators: +12
- Has justifications: +10
- Has source docs: +8
- Has next_step: +5
- Blockers documented: +2
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from database import get_supabase
from services.opportunity_confidence import evaluate_opportunity_confidence


def main():
    """Evaluate confidence for all opportunities."""
    supabase = get_supabase()

    # Get all opportunities
    print("Fetching opportunities...")
    result = supabase.table("ai_opportunities").select("*").execute()
    opportunities = result.data

    if not opportunities:
        print("No opportunities found.")
        return

    print(f"Found {len(opportunities)} opportunities\n")

    # Track stats
    updated = 0
    by_level = {"high": 0, "moderate": 0, "low": 0, "very_low": 0}
    all_confidences = []

    for opp in opportunities:
        title = opp.get("title", "Untitled")[:50]
        opp_id = opp["id"]

        # Evaluate confidence
        confidence, questions = evaluate_opportunity_confidence(opp)
        all_confidences.append(confidence)

        # Determine level
        if confidence >= 80:
            level = "high"
        elif confidence >= 60:
            level = "moderate"
        elif confidence >= 40:
            level = "low"
        else:
            level = "very_low"
        by_level[level] += 1

        # Update in database
        try:
            supabase.table("ai_opportunities").update({
                "scoring_confidence": confidence,
                "confidence_questions": questions,
            }).eq("id", opp_id).execute()
            updated += 1
            print(f"  [{confidence:3d}%] {level:8s} | {title}... ({len(questions)} questions)")
        except Exception as e:
            print(f"  [ERROR] Failed to update {title}: {e}")

    # Summary
    avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total opportunities: {len(opportunities)}")
    print(f"Successfully updated: {updated}")
    print(f"Average confidence: {avg_confidence:.1f}%")
    print(f"\nDistribution:")
    print(f"  High (80-100%):     {by_level['high']:3d}")
    print(f"  Moderate (60-79%):  {by_level['moderate']:3d}")
    print(f"  Low (40-59%):       {by_level['low']:3d}")
    print(f"  Very Low (<40%):    {by_level['very_low']:3d}")


if __name__ == "__main__":
    main()
