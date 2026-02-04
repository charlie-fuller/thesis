#!/usr/bin/env python3
"""Migrate Project-Triage Markdown Data to Thesis PostgreSQL.

This script imports data from the project-triage markdown files into the
thesis database. It handles:
- Opportunities from master-opportunities-index.md
- Stakeholder profiles from profiles/*.md
- Metrics from profiles/metrics-and-kpis.md

Usage:
    # Preview what would be imported (dry-run)
    python migrate_project_triage.py --dry-run

    # Actually perform the migration
    python migrate_project_triage.py

    # Specify custom source directory
    python migrate_project_triage.py --source /path/to/project-triage

Requirements:
    - SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables
    - Or specify via --supabase-url and --supabase-key arguments
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Optional

# Add the parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from supabase import Client, create_client
except ImportError:
    print("Error: supabase package not installed. Run: pip install supabase")
    sys.exit(1)


# ============================================================================
# PARSING FUNCTIONS
# ============================================================================


def parse_opportunities_markdown(filepath: str) -> list[dict]:
    """Parse master-opportunities-index.md into opportunity records.

    Looks for markdown tables with columns:
    | ID | Opportunity | Owner | ROI | Effort | Strategic | Readiness | Total | Status |
    """
    opportunities = []

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all tables with opportunity data
    # Match tables that have ID column and score columns
    table_pattern = r"\|[^\n]*ID[^\n]*\|\n\|[-\s|]+\|\n((?:\|[^\n]+\|\n)+)"
    tables = re.findall(table_pattern, content, re.IGNORECASE)

    for table_content in tables:
        rows = table_content.strip().split("\n")
        for row in rows:
            # Skip empty rows or separator rows
            if not row.strip() or row.strip().startswith("|--"):
                continue

            # Parse the row
            cols = [c.strip() for c in row.split("|")[1:-1]]  # Remove first/last empty

            if len(cols) >= 8:
                # Extract data
                opp_id = cols[0].strip().replace("**", "")
                title = cols[1].strip().replace("**", "")
                owner = cols[2].strip()
                roi = _parse_score(cols[3])
                effort = _parse_score(cols[4])
                strategic = _parse_score(cols[5])
                readiness = _parse_score(cols[6])
                _parse_score(cols[7]) if len(cols) > 7 else None
                status = cols[8].strip() if len(cols) > 8 else "identified"

                # Skip if ID doesn't match pattern (e.g., S01, F02, etc.)
                if not re.match(r"^[A-Z]\d+$", opp_id):
                    continue

                # Determine department from ID prefix
                dept_map = {
                    "S": "sales",
                    "O": "onboarding",
                    "F": "finance",
                    "L": "legal",
                    "H": "hr",
                    "T": "it",
                    "M": "marketing",
                    "P": "productivity",
                }
                department = dept_map.get(opp_id[0], "other")

                opportunities.append(
                    {
                        "opportunity_code": opp_id,
                        "title": title,
                        "owner_name": owner,
                        "department": department,
                        "roi_potential": roi,
                        "implementation_effort": effort,
                        "strategic_alignment": strategic,
                        "stakeholder_readiness": readiness,
                        "status": _normalize_status(status),
                    }
                )

    return opportunities


def _parse_score(value: str) -> Optional[int]:
    """Parse a score value, handling bold markers and non-numeric values."""
    value = value.strip().replace("**", "")
    try:
        score = int(value)
        return score if 1 <= score <= 5 else None
    except ValueError:
        return None


def _normalize_status(status: str) -> str:
    """Normalize status strings to valid enum values."""
    status_lower = status.lower().strip()

    # Map common variations to valid values
    status_map = {
        "identified": "identified",
        "scoping": "scoping",
        "pilot": "pilot",
        "scaling": "scaling",
        "completed": "completed",
        "blocked": "blocked",
        # Common variations
        "in progress": "scoping",
        "prototype exists": "scoping",
        "working prototype": "pilot",
        "demo'd": "scoping",
        "poc built": "scoping",
        "berlin workshop": "identified",
        "need to identify": "identified",
        "referenced": "identified",
        "legal concerns": "blocked",
        "data silos": "blocked",
    }

    for key, val in status_map.items():
        if key in status_lower:
            return val

    return "identified"


def parse_stakeholder_profile(filepath: str) -> dict:
    """Parse a stakeholder profile markdown file.

    Extracts:
    - Leader name, title, reports_to, team_size
    - Pain points
    - AI priorities/opportunities
    - Win conditions
    - Communication preferences
    - Open questions
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    profile = {
        "name": None,
        "role": None,
        "department": None,
        "reports_to_name": None,
        "team_size": None,
        "ai_priorities": [],
        "pain_points": [],
        "win_conditions": [],
        "communication_style": None,
        "open_questions": [],
    }

    # Extract leader info
    leader_match = re.search(r"\*\*Leader:\*\*\s*([^,\n]+)", content)
    if leader_match:
        profile["name"] = leader_match.group(1).strip()

    # Extract role from leader line or title
    role_match = re.search(r"Leader:\*\*\s*[^,]+,\s*([^\n]+)", content)
    if role_match:
        profile["role"] = role_match.group(1).strip()

    # Extract reports to
    reports_match = re.search(r"\*\*Reports to:\*\*\s*([^\n(]+)", content)
    if reports_match:
        profile["reports_to_name"] = reports_match.group(1).strip()

    # Extract team size
    team_match = re.search(r"\*\*Team Size:\*\*\s*(\d+)", content)
    if team_match:
        profile["team_size"] = int(team_match.group(1))

    # Extract department from filename
    filename = Path(filepath).stem
    dept_map = {
        "finance": "finance",
        "legal": "legal",
        "hr-talent": "hr",
        "hr-employee": "hr",
        "information-services": "it",
        "revops": "revops",
    }
    for key, dept in dept_map.items():
        if key in filename.lower():
            profile["department"] = dept
            break

    # Extract pain points
    pain_section = re.search(r"## Pain Points[^\n]*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if pain_section:
        pain_items = re.findall(r"[-*]\s*\*\*([^*]+)\*\*[:\s]*([^\n]+)", pain_section.group(1))
        profile["pain_points"] = [f"{item[0]}: {item[1]}" for item in pain_items[:10]]

    # Extract AI priorities from opportunities section
    opp_section = re.search(r"## AI Opportunities[^\n]*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if opp_section:
        opp_items = re.findall(r"\|\s*[A-Z]\d+\s*\|\s*\*?\*?([^|*]+)", opp_section.group(1))
        profile["ai_priorities"] = [item.strip() for item in opp_items if item.strip()][:5]

    # Extract win conditions
    win_section = re.search(r"## Win Conditions[^\n]*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if win_section:
        win_items = re.findall(r"[-*]\s+([^\n]+)", win_section.group(1))
        profile["win_conditions"] = [item.strip() for item in win_items if item.strip()][:5]

    # Extract communication style
    comm_section = re.search(r"## Communication Preferences[^\n]*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if comm_section:
        style_match = re.search(r"\*\*Style:\*\*\s*([^\n]+)", comm_section.group(1))
        if style_match:
            profile["communication_style"] = style_match.group(1).strip()
        else:
            # Take first few sentences as style
            text = comm_section.group(1).strip()[:500]
            profile["communication_style"] = text

    # Extract open questions
    questions_section = re.search(r"## Questions to Explore[^\n]*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if questions_section:
        q_items = re.findall(r"\d+\.\s*([^\n]+)", questions_section.group(1))
        profile["open_questions"] = [q.strip() for q in q_items if q.strip()][:10]

    return profile


def parse_metrics_markdown(filepath: str) -> list[dict]:
    """Parse metrics-and-kpis.md into stakeholder metric records.

    Returns list of:
    {
        'stakeholder_name': str,
        'metric_name': str,
        'current_value': str,
        'target_value': str,
        'validation_status': str,  # red, yellow, green
        'source': str,
    }
    """
    metrics = []

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by section headers to identify stakeholder
    sections = re.split(r"\n## ([^\n]+)", content)

    current_stakeholder = None
    for i, section in enumerate(sections):
        # Check if this is a header
        if i % 2 == 1:  # Odd indices are headers
            # Extract stakeholder name from header
            name_match = re.search(r"(Finance|Legal|HR|IT|RevOps)[^\(]*\(([^)]+)\)", section)
            if name_match:
                current_stakeholder = name_match.group(2).strip()
            continue

        if not current_stakeholder:
            continue

        # Find metric tables in this section
        table_pattern = r"\|[^\n]*Metric[^\n]*\|\n\|[-\s|]+\|\n((?:\|[^\n]+\|\n)+)"
        tables = re.findall(table_pattern, section, re.IGNORECASE)

        for table_content in tables:
            rows = table_content.strip().split("\n")
            for row in rows:
                cols = [c.strip() for c in row.split("|")[1:-1]]

                if len(cols) >= 3:
                    metric_name = cols[0].strip().replace("**", "")
                    current_value = cols[1].strip() if len(cols) > 1 else None
                    target_value = cols[2].strip() if len(cols) > 2 else None

                    # Try to detect validation status from Status column or emoji
                    validation_status = "red"
                    if len(cols) > 3:
                        status_col = cols[3].lower()
                        if "🟢" in cols[3] or "confirmed" in status_col or "validated" in status_col:
                            validation_status = "green"
                        elif "🟡" in cols[3] or "estimated" in status_col or "partial" in status_col:
                            validation_status = "yellow"

                    source = cols[4] if len(cols) > 4 else None

                    if metric_name and not metric_name.startswith("-"):
                        metrics.append(
                            {
                                "stakeholder_name": current_stakeholder,
                                "metric_name": metric_name,
                                "current_value": current_value,
                                "target_value": target_value,
                                "validation_status": validation_status,
                                "source": source,
                            }
                        )

    return metrics


# ============================================================================
# MIGRATION FUNCTIONS
# ============================================================================


def get_or_create_stakeholder(supabase: Client, client_id: str, name: str, profile: dict = None) -> str:
    """Get existing stakeholder by name or create new one. Returns stakeholder ID."""
    # Try to find existing
    result = (
        supabase.table("stakeholders")
        .select("id")
        .eq("client_id", client_id)
        .ilike("name", f"%{name.split()[0]}%")
        .execute()
    )

    if result.data:
        return result.data[0]["id"]

    # Create new stakeholder
    data = {
        "client_id": client_id,
        "name": name,
        "organization": "Contentful",
    }

    if profile:
        data.update(
            {
                "role": profile.get("role"),
                "department": profile.get("department"),
                "reports_to_name": profile.get("reports_to_name"),
                "team_size": profile.get("team_size"),
                "ai_priorities": profile.get("ai_priorities"),
                "pain_points": profile.get("pain_points"),
                "win_conditions": profile.get("win_conditions"),
                "communication_style": profile.get("communication_style"),
                "open_questions": profile.get("open_questions"),
                "priority_level": "tier_2",  # Default to tier_2
                "relationship_status": "building",
            }
        )

    result = supabase.table("stakeholders").insert(data).execute()
    return result.data[0]["id"]


def migrate_opportunities(supabase: Client, client_id: str, opportunities: list[dict], dry_run: bool = False):
    """Insert or update opportunities in database."""
    results = {"created": 0, "updated": 0, "errors": []}

    # Build stakeholder name -> ID cache
    stakeholder_cache = {}

    for opp in opportunities:
        try:
            # Look up owner stakeholder
            owner_name = opp.pop("owner_name", None)
            owner_id = None
            if owner_name and owner_name not in ("TBD", "-", ""):
                if owner_name not in stakeholder_cache:
                    stakeholder_cache[owner_name] = get_or_create_stakeholder(supabase, client_id, owner_name)
                owner_id = stakeholder_cache[owner_name]

            if dry_run:
                print(f"  [DRY-RUN] Would create opportunity: {opp['opportunity_code']} - {opp['title']}")
                results["created"] += 1
                continue

            # Check if opportunity exists
            existing = (
                supabase.table("ai_opportunities")
                .select("id")
                .eq("client_id", client_id)
                .eq("opportunity_code", opp["opportunity_code"])
                .execute()
            )

            data = {"client_id": client_id, "owner_stakeholder_id": owner_id, **opp}

            if existing.data:
                # Update
                supabase.table("ai_opportunities").update(data).eq("id", existing.data[0]["id"]).execute()
                results["updated"] += 1
            else:
                # Insert
                supabase.table("ai_opportunities").insert(data).execute()
                results["created"] += 1

        except Exception as e:
            results["errors"].append(f"{opp.get('opportunity_code', 'unknown')}: {str(e)}")

    return results


def migrate_stakeholder_profiles(supabase: Client, client_id: str, profiles: list[dict], dry_run: bool = False):
    """Update stakeholder profiles with project-triage fields."""
    results = {"updated": 0, "created": 0, "errors": []}

    for profile in profiles:
        if not profile.get("name"):
            continue

        try:
            if dry_run:
                print(f"  [DRY-RUN] Would update stakeholder: {profile['name']}")
                results["updated"] += 1
                continue

            # Find or create stakeholder
            stakeholder_id = get_or_create_stakeholder(supabase, client_id, profile["name"], profile)

            # Update with profile data
            update_data = {
                "role": profile.get("role"),
                "department": profile.get("department"),
                "reports_to_name": profile.get("reports_to_name"),
                "team_size": profile.get("team_size"),
                "ai_priorities": profile.get("ai_priorities"),
                "pain_points": profile.get("pain_points"),
                "win_conditions": profile.get("win_conditions"),
                "communication_style": profile.get("communication_style"),
                "open_questions": profile.get("open_questions"),
                "priority_level": "tier_2",
                "relationship_status": "building",
            }

            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}

            supabase.table("stakeholders").update(update_data).eq("id", stakeholder_id).execute()

            results["updated"] += 1

        except Exception as e:
            results["errors"].append(f"{profile.get('name', 'unknown')}: {str(e)}")

    return results


def migrate_metrics(supabase: Client, client_id: str, metrics: list[dict], dry_run: bool = False):
    """Insert stakeholder metrics with validation status."""
    results = {"created": 0, "skipped": 0, "errors": []}

    # Build stakeholder name -> ID cache
    stakeholder_cache = {}

    for metric in metrics:
        try:
            stakeholder_name = metric.pop("stakeholder_name", None)
            if not stakeholder_name:
                results["skipped"] += 1
                continue

            # Get stakeholder ID
            if stakeholder_name not in stakeholder_cache:
                # Try to find stakeholder
                result = (
                    supabase.table("stakeholders")
                    .select("id")
                    .eq("client_id", client_id)
                    .ilike("name", f"%{stakeholder_name.split()[0]}%")
                    .execute()
                )

                if result.data:
                    stakeholder_cache[stakeholder_name] = result.data[0]["id"]
                else:
                    results["skipped"] += 1
                    continue

            stakeholder_id = stakeholder_cache[stakeholder_name]

            if dry_run:
                print(f"  [DRY-RUN] Would create metric: {metric['metric_name']} for {stakeholder_name}")
                results["created"] += 1
                continue

            # Check if metric exists
            existing = (
                supabase.table("stakeholder_metrics")
                .select("id")
                .eq("stakeholder_id", stakeholder_id)
                .eq("metric_name", metric["metric_name"])
                .execute()
            )

            data = {
                "client_id": client_id,
                "stakeholder_id": stakeholder_id,
                "metric_name": metric["metric_name"],
                "current_value": metric.get("current_value"),
                "target_value": metric.get("target_value"),
                "validation_status": metric.get("validation_status", "red"),
                "source": metric.get("source"),
            }

            if existing.data:
                # Update
                supabase.table("stakeholder_metrics").update(data).eq("id", existing.data[0]["id"]).execute()
            else:
                # Insert
                supabase.table("stakeholder_metrics").insert(data).execute()

            results["created"] += 1

        except Exception as e:
            results["errors"].append(f"{metric.get('metric_name', 'unknown')}: {str(e)}")

    return results


# ============================================================================
# MAIN
# ============================================================================


def main():
    parser = argparse.ArgumentParser(description="Migrate project-triage data to thesis database")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing to database")
    parser.add_argument(
        "--source",
        type=str,
        help="Path to project-triage directory",
        default="/Users/charlie.fuller/vaults/Contentful/agents/project-triage",
    )
    parser.add_argument("--supabase-url", type=str, help="Supabase URL (or set SUPABASE_URL env var)")
    parser.add_argument(
        "--supabase-key",
        type=str,
        help="Supabase service key (or set SUPABASE_SERVICE_ROLE_KEY env var)",
    )
    parser.add_argument("--client-id", type=str, help="Client ID to migrate data into")

    args = parser.parse_args()

    # Get Supabase credentials
    supabase_url = args.supabase_url or os.environ.get("SUPABASE_URL")
    supabase_key = (
        args.supabase_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
    )

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        print("Set via environment variables or --supabase-url and --supabase-key arguments")
        sys.exit(1)

    # Verify source directory exists
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: Source directory not found: {args.source}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print("Project-Triage Migration to Thesis")
    print(f"{'=' * 60}")
    print(f"Source: {args.source}")
    print(f"Dry run: {args.dry_run}")
    print()

    # Connect to Supabase
    if not args.dry_run:
        try:
            supabase = create_client(supabase_url, supabase_key)
            print("✅ Connected to Supabase")
        except Exception as e:
            print(f"Error connecting to Supabase: {e}")
            sys.exit(1)
    else:
        supabase = None
        print("🔍 DRY RUN MODE - No database changes will be made")

    # Get or prompt for client_id
    client_id = args.client_id
    if not client_id and not args.dry_run:
        # Try to get first client
        clients = supabase.table("clients").select("id, name").limit(1).execute()
        if clients.data:
            client_id = clients.data[0]["id"]
            print(f"Using client: {clients.data[0]['name']} ({client_id})")
        else:
            print("Error: No clients found. Please specify --client-id")
            sys.exit(1)
    elif args.dry_run:
        client_id = "dry-run-client-id"

    print()

    # =========================================================================
    # 1. Parse and migrate opportunities
    # =========================================================================
    print("📊 Parsing opportunities...")
    opportunities_file = source_path / "master-opportunities-index.md"
    if opportunities_file.exists():
        opportunities = parse_opportunities_markdown(str(opportunities_file))
        print(f"   Found {len(opportunities)} opportunities")

        if not args.dry_run:
            print("   Migrating opportunities...")
            results = migrate_opportunities(supabase, client_id, opportunities, args.dry_run)
            print(f"   ✅ Created: {results['created']}, Updated: {results['updated']}")
            if results["errors"]:
                print(f"   ⚠️ Errors: {len(results['errors'])}")
                for err in results["errors"][:5]:
                    print(f"      - {err}")
        else:
            for opp in opportunities[:10]:
                print(f"   - {opp['opportunity_code']}: {opp['title']}")
            if len(opportunities) > 10:
                print(f"   ... and {len(opportunities) - 10} more")
    else:
        print(f"   ⚠️ File not found: {opportunities_file}")

    print()

    # =========================================================================
    # 2. Parse and migrate stakeholder profiles
    # =========================================================================
    print("👤 Parsing stakeholder profiles...")
    profiles_dir = source_path / "profiles"
    profiles = []
    if profiles_dir.exists():
        for profile_file in profiles_dir.glob("*.md"):
            if profile_file.name in (
                "PROFILE-TEMPLATE.md",
                "metrics-and-kpis.md",
                "GNA-SYSTEMS-VIEW.md",
            ):
                continue
            profile = parse_stakeholder_profile(str(profile_file))
            if profile.get("name"):
                profiles.append(profile)
                print(f"   Found: {profile['name']}")

        print(f"   Found {len(profiles)} profiles")

        if not args.dry_run:
            print("   Migrating profiles...")
            results = migrate_stakeholder_profiles(supabase, client_id, profiles, args.dry_run)
            print(f"   ✅ Updated: {results['updated']}")
            if results["errors"]:
                print(f"   ⚠️ Errors: {len(results['errors'])}")
    else:
        print(f"   ⚠️ Directory not found: {profiles_dir}")

    print()

    # =========================================================================
    # 3. Parse and migrate metrics
    # =========================================================================
    print("📈 Parsing metrics...")
    metrics_file = source_path / "profiles" / "metrics-and-kpis.md"
    if metrics_file.exists():
        metrics = parse_metrics_markdown(str(metrics_file))
        print(f"   Found {len(metrics)} metrics")

        if not args.dry_run:
            print("   Migrating metrics...")
            results = migrate_metrics(supabase, client_id, metrics, args.dry_run)
            print(f"   ✅ Created: {results['created']}, Skipped: {results['skipped']}")
            if results["errors"]:
                print(f"   ⚠️ Errors: {len(results['errors'])}")
        else:
            for metric in metrics[:10]:
                print(f"   - {metric['stakeholder_name']}: {metric['metric_name']}")
            if len(metrics) > 10:
                print(f"   ... and {len(metrics) - 10} more")
    else:
        print(f"   ⚠️ File not found: {metrics_file}")

    print()
    print(f"{'=' * 60}")
    print("Migration complete!")
    if args.dry_run:
        print("This was a DRY RUN. No changes were made to the database.")
        print("Run without --dry-run to actually migrate the data.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
