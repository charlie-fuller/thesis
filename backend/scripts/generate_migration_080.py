#!/usr/bin/env python3
"""Generate migration 080: Performance fixes for Supabase advisory warnings.

Connects to the live Supabase DB and generates SQL to fix:
1. auth_rls_initplan: Replace auth.uid()/auth.role() with (SELECT ...) in RLS policies
2. multiple_permissive_policies: Add TO service_role, drop redundant SELECT policies
3. duplicate_index: Drop idx_docs_user_date
4. unindexed_foreign_keys: Create missing FK indexes
5. unused_index: Drop 178 unused indexes (keeping embedding/vector indexes)

Usage:
    cd backend
    SUPABASE_DB_PASSWORD="$(op read 'op://Employee/Thesis Backend/SUPABASE_DB_PASSWORD')" \
    .venv/bin/python scripts/generate_migration_080.py > ../database/migrations/080_performance_fixes.sql
"""

import os
import re
import sys
from collections import defaultdict

import psycopg2
from psycopg2.extras import RealDictCursor

PROJECT_REF = "imdavfgreeddxluslsdl"
POOLER_HOST = "aws-1-us-east-2.pooler.supabase.com"
POOLER_PORT = 5432

# Indexes to KEEP even if unused -- these are used by vector search functions,
# or are unique constraints, or serve as covering indexes for FKs we're about to create.
# Embedding/vector indexes are critical for RAG similarity search via match_*() functions.
KEEP_INDEXES = {
    # Vector embedding indexes -- used by match_documents() and similar RPC functions
    "idx_disco_chunks_embedding",
    "idx_purdy_chunks_embedding",
    "idx_purdy_system_kb_embedding",
    "idx_task_candidates_embedding",
    "idx_project_tasks_embedding",
    "help_chunks_embedding_idx",
    # idx_documents_uploaded_by_at is kept (its duplicate idx_docs_user_date is dropped instead)
    "idx_documents_uploaded_by_at",
}


def get_connection():
    password = os.environ.get("SUPABASE_DB_PASSWORD")
    if not password:
        print("ERROR: SUPABASE_DB_PASSWORD not set", file=sys.stderr)
        sys.exit(1)

    conn_str = (
        f"postgresql://postgres.{PROJECT_REF}:{password}" f"@{POOLER_HOST}:{POOLER_PORT}/postgres?sslmode=require"
    )
    return psycopg2.connect(conn_str)


def fetch_policies(cur):
    """Fetch all public schema RLS policies with their definitions."""
    cur.execute("""
        SELECT
            schemaname,
            tablename,
            policyname,
            permissive,
            roles,
            cmd,
            qual,
            with_check
        FROM pg_policies
        WHERE schemaname = 'public'
        ORDER BY tablename, policyname
    """)
    return cur.fetchall()


def fetch_existing_indexes(cur):
    """Fetch all existing indexes in public schema."""
    cur.execute("""
        SELECT
            indexname,
            tablename,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname
    """)
    return cur.fetchall()


def fetch_unused_indexes(cur):
    """Fetch indexes with zero scans from pg_stat_user_indexes."""
    cur.execute("""
        SELECT
            s.schemaname,
            s.relname AS tablename,
            s.indexrelname AS indexname,
            s.idx_scan,
            pg_relation_size(s.indexrelid) AS index_size,
            i.indexdef
        FROM pg_stat_user_indexes s
        JOIN pg_indexes i ON s.indexrelname = i.indexname AND s.schemaname = i.schemaname
        WHERE s.schemaname = 'public'
            AND s.idx_scan = 0
            AND s.indexrelname NOT LIKE '%_pkey'
            AND i.indexdef NOT LIKE '%UNIQUE%'
        ORDER BY pg_relation_size(s.indexrelid) DESC
    """)
    return cur.fetchall()


def fetch_foreign_keys(cur):
    """Fetch all foreign keys in public schema with their columns."""
    cur.execute("""
        SELECT
            tc.table_name,
            kcu.column_name,
            tc.constraint_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
            AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        ORDER BY tc.table_name, kcu.column_name
    """)
    return cur.fetchall()


def needs_initplan_fix(qual, with_check):
    """Check if a policy has bare auth.uid() or auth.role() calls."""
    for expr in [qual, with_check]:
        if not expr:
            continue
        # Match auth.uid() NOT already wrapped in (SELECT auth.uid())
        # We look for auth.uid() that isn't preceded by "SELECT "
        if re.search(r"(?<!\(SELECT )auth\.uid\(\)", expr):
            return True
        if re.search(r"(?<!\(SELECT )auth\.role\(\)", expr):
            return True
    return False


def fix_initplan_expr(expr):
    """Replace bare auth.uid() and auth.role() with (SELECT ...) versions."""
    if not expr:
        return expr

    # Replace auth.uid() -> (SELECT auth.uid()) but not if already wrapped
    # First, temporarily mark already-wrapped ones
    result = expr
    result = result.replace("(SELECT auth.uid())", "__WRAPPED_UID__")
    result = result.replace("(select auth.uid())", "__WRAPPED_UID_LC__")
    result = result.replace("auth.uid()", "(SELECT auth.uid())")
    result = result.replace("__WRAPPED_UID__", "(SELECT auth.uid())")
    result = result.replace("__WRAPPED_UID_LC__", "(SELECT auth.uid())")

    # Same for auth.role()
    result = result.replace("(SELECT auth.role())", "__WRAPPED_ROLE__")
    result = result.replace("(select auth.role())", "__WRAPPED_ROLE_LC__")
    result = result.replace("auth.role()", "(SELECT auth.role())")
    result = result.replace("__WRAPPED_ROLE__", "(SELECT auth.role())")
    result = result.replace("__WRAPPED_ROLE_LC__", "(SELECT auth.role())")

    return result


def is_service_role_policy(policy):
    """Check if this policy is meant for service_role access."""
    roles = policy["roles"]
    qual = policy["qual"] or ""
    # Service role policies typically have auth.role() = 'service_role' in USING
    if "service_role" in qual.lower():
        return True
    # Or they might check current_setting for role
    if "current_setting" in qual.lower() and "service_role" in qual.lower():
        return True
    return False


def format_roles(roles):
    """Format roles array from pg_policies into SQL."""
    if not roles:
        return "PUBLIC"
    # psycopg2 returns roles as a Python list like ['{authenticated}'] or ['authenticated']
    if isinstance(roles, list):
        # Flatten and clean
        cleaned = []
        for r in roles:
            r = str(r).strip("{}")
            for part in r.split(","):
                part = part.strip()
                if part:
                    cleaned.append(part)
        return ", ".join(cleaned) if cleaned else "PUBLIC"
    # Fallback for string format
    roles_str = str(roles).strip("{}")
    parts = [r.strip() for r in roles_str.split(",") if r.strip()]
    return ", ".join(parts) if parts else "PUBLIC"


def format_cmd(cmd):
    """Format command for CREATE POLICY."""
    # pg_policies returns ALL, SELECT, INSERT, UPDATE, DELETE
    return cmd.upper()


def escape_sql_string(s):
    """Escape single quotes in SQL expressions for use in policy definitions."""
    if not s:
        return s
    return s.replace("'", "''")


def generate_policy_sql(policy, new_qual=None, new_with_check=None, new_roles=None):
    """Generate DROP + CREATE POLICY SQL."""
    table = policy["tablename"]
    name = policy["policyname"]
    permissive = "PERMISSIVE" if policy["permissive"] == "PERMISSIVE" else "RESTRICTIVE"
    cmd = format_cmd(policy["cmd"])
    roles = new_roles or format_roles(policy["roles"])
    qual = new_qual if new_qual is not None else policy["qual"]
    with_check = new_with_check if new_with_check is not None else policy["with_check"]

    lines = []
    lines.append(f'DROP POLICY IF EXISTS "{name}" ON public.{table};')
    lines.append(f'CREATE POLICY "{name}" ON public.{table}')
    lines.append(f"  AS {permissive}")
    lines.append(f"  FOR {cmd}")
    lines.append(f"  TO {roles}")

    if qual:
        lines.append(f"  USING ({qual})")

    if with_check:
        lines.append(f"  WITH CHECK ({with_check})")

    # End with semicolon
    lines[-1] += ";"

    return "\n".join(lines)


def main():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("-- Migration 080: Performance fixes", file=sys.stderr)
    print("-- Fetching policies...", file=sys.stderr)
    policies = fetch_policies(cur)
    print(f"-- Found {len(policies)} policies", file=sys.stderr)

    print("-- Fetching indexes...", file=sys.stderr)
    indexes = fetch_existing_indexes(cur)
    print(f"-- Found {len(indexes)} indexes", file=sys.stderr)

    print("-- Fetching foreign keys...", file=sys.stderr)
    fks = fetch_foreign_keys(cur)
    print(f"-- Found {len(fks)} foreign keys", file=sys.stderr)

    print("-- Fetching unused indexes...", file=sys.stderr)
    unused_indexes = fetch_unused_indexes(cur)
    print(f"-- Found {len(unused_indexes)} unused indexes (0 scans)", file=sys.stderr)

    cur.close()
    conn.close()

    # Build index lookup: (table, column) -> list of index definitions
    index_lookup = defaultdict(list)
    index_names = set()
    for idx in indexes:
        index_names.add(idx["indexname"])
        # Extract columns from indexdef
        idx_def = idx["indexdef"]
        index_lookup[idx["tablename"]].append(idx_def)

    # ================================================================
    # Start generating SQL
    # ================================================================
    sql_parts = []

    sql_parts.append("-- =============================================================")
    sql_parts.append("-- Migration 080: Performance Fixes")
    sql_parts.append("-- Fixes auth_rls_initplan, multiple_permissive_policies,")
    sql_parts.append("-- duplicate_index, unindexed_foreign_keys, and unused_index advisories")
    sql_parts.append("-- =============================================================")
    sql_parts.append("")
    sql_parts.append("BEGIN;")
    sql_parts.append("")

    # ----------------------------------------------------------------
    # 1. Fix auth_rls_initplan: wrap auth.uid()/auth.role() in (SELECT ...)
    # ----------------------------------------------------------------
    sql_parts.append("-- =============================================================")
    sql_parts.append("-- SECTION 1: Fix auth_rls_initplan")
    sql_parts.append("-- Wrap bare auth.uid()/auth.role() in (SELECT ...) subselects")
    sql_parts.append("-- =============================================================")
    sql_parts.append("")

    initplan_count = 0
    # Track which policies we've already rewritten (for dedup with section 2)
    rewritten_policies = set()

    for p in policies:
        if needs_initplan_fix(p["qual"], p["with_check"]):
            new_qual = fix_initplan_expr(p["qual"])
            new_with_check = fix_initplan_expr(p["with_check"])

            # Check if this is a service_role policy that should also get TO service_role
            new_roles = None
            if is_service_role_policy(p):
                new_roles = "service_role"
                # Simplify the USING clause since TO service_role handles access control
                new_qual = "true"
                new_with_check = None if p["cmd"] in ("SELECT", "DELETE") else "true" if p["with_check"] else None

            policy_sql = generate_policy_sql(p, new_qual, new_with_check, new_roles)
            sql_parts.append(f"-- Table: {p['tablename']}, Policy: {p['policyname']}")
            sql_parts.append(policy_sql)
            sql_parts.append("")
            initplan_count += 1
            rewritten_policies.add((p["tablename"], p["policyname"]))

    sql_parts.append(f"-- Total auth_rls_initplan policies fixed: {initplan_count}")
    sql_parts.append("")

    # ----------------------------------------------------------------
    # 2. Fix multiple_permissive_policies
    # ----------------------------------------------------------------
    sql_parts.append("-- =============================================================")
    sql_parts.append("-- SECTION 2: Fix multiple_permissive_policies")
    sql_parts.append("-- Convert service_role policies to TO service_role,")
    sql_parts.append("-- drop redundant SELECT policies covered by FOR ALL")
    sql_parts.append("-- =============================================================")
    sql_parts.append("")

    # Group permissive policies by (table, cmd)
    permissive_groups = defaultdict(list)
    for p in policies:
        if p["permissive"] == "PERMISSIVE":
            cmd = p["cmd"]
            # FOR ALL policies apply to all commands
            permissive_groups[(p["tablename"], cmd)].append(p)

    multi_perm_count = 0
    dropped_redundant = 0

    for (table, cmd), group in sorted(permissive_groups.items()):
        if len(group) <= 1:
            continue

        # Check for service_role policies not yet rewritten
        for p in group:
            key = (p["tablename"], p["policyname"])
            if key in rewritten_policies:
                continue

            if is_service_role_policy(p) and not p.get("_rewritten"):
                # Rewrite to TO service_role
                policy_sql = generate_policy_sql(
                    p,
                    new_qual="true",
                    new_with_check="true" if p["with_check"] else None,
                    new_roles="service_role",
                )
                sql_parts.append(f"-- Table: {table}, Policy: {p['policyname']} (-> TO service_role)")
                sql_parts.append(policy_sql)
                sql_parts.append("")
                multi_perm_count += 1
                rewritten_policies.add(key)

    # Now check for redundant SELECT policies where FOR ALL exists
    all_policies_by_table = defaultdict(list)
    for p in policies:
        if p["permissive"] == "PERMISSIVE":
            all_policies_by_table[p["tablename"]].append(p)

    for table, table_policies in sorted(all_policies_by_table.items()):
        for_all = [p for p in table_policies if p["cmd"] == "*"]  # pg_policies uses * for ALL
        for_select = [p for p in table_policies if p["cmd"] == "r"]  # r = SELECT

        if not for_all or not for_select:
            continue

        # If a FOR ALL policy has the same or broader USING as a SELECT policy, drop the SELECT one
        for sel_p in for_select:
            key = (sel_p["tablename"], sel_p["policyname"])
            if key in rewritten_policies:
                continue

            for all_p in for_all:
                # Same roles and same/broader qual means SELECT is redundant
                if sel_p["roles"] == all_p["roles"] and sel_p["qual"] == all_p["qual"]:
                    sql_parts.append(f"-- Redundant SELECT policy (covered by FOR ALL): {sel_p['policyname']}")
                    sql_parts.append(f'DROP POLICY IF EXISTS "{sel_p["policyname"]}" ON public.{table};')
                    sql_parts.append("")
                    dropped_redundant += 1
                    rewritten_policies.add(key)
                    break

    sql_parts.append(f"-- Total multiple_permissive fixes: {multi_perm_count} rewritten, {dropped_redundant} dropped")
    sql_parts.append("")

    # ----------------------------------------------------------------
    # 3. Fix duplicate_index
    # ----------------------------------------------------------------
    sql_parts.append("-- =============================================================")
    sql_parts.append("-- SECTION 3: Drop duplicate index")
    sql_parts.append("-- =============================================================")
    sql_parts.append("")

    if "idx_docs_user_date" in index_names:
        sql_parts.append("-- idx_docs_user_date duplicates idx_documents_uploaded_by_at")
        sql_parts.append("DROP INDEX IF EXISTS idx_docs_user_date;")
    else:
        sql_parts.append("-- idx_docs_user_date already removed or not found")

    sql_parts.append("")

    # ----------------------------------------------------------------
    # 4. Fix unindexed_foreign_keys
    # ----------------------------------------------------------------
    sql_parts.append("-- =============================================================")
    sql_parts.append("-- SECTION 4: Create missing indexes for foreign keys")
    sql_parts.append("-- =============================================================")
    sql_parts.append("")

    fk_index_count = 0
    for fk in fks:
        table = fk["table_name"]
        column = fk["column_name"]
        idx_name = f"idx_{table}_{column}"

        # Check if an index already exists on this column
        has_index = False
        for idx_def in index_lookup.get(table, []):
            # Check if this column is the leading column of any index
            # indexdef looks like: CREATE INDEX idx_name ON public.table USING btree (column)
            # We need to check if column appears as a leading key
            col_pattern = rf"\({column}(?:\s|,|\))"
            if re.search(col_pattern, idx_def):
                has_index = True
                break

        if not has_index:
            sql_parts.append(f"CREATE INDEX IF NOT EXISTS {idx_name} ON public.{table} ({column});")
            fk_index_count += 1

    sql_parts.append("")
    sql_parts.append(f"-- Total FK indexes created: {fk_index_count}")
    sql_parts.append("")

    # ----------------------------------------------------------------
    # 5. Drop unused indexes
    # ----------------------------------------------------------------
    sql_parts.append("-- =============================================================")
    sql_parts.append("-- SECTION 5: Drop unused indexes (0 scans since last stats reset)")
    sql_parts.append("-- Excludes: primary keys, unique constraints, embedding/vector indexes")
    sql_parts.append("-- =============================================================")
    sql_parts.append("")

    # Also build set of FK index names we're about to create in section 4
    # so we don't drop something we just created
    fk_index_names_to_create = set()
    for fk in fks:
        fk_index_names_to_create.add(f"idx_{fk['table_name']}_{fk['column_name']}")

    unused_drop_count = 0
    unused_kept_count = 0
    for idx in unused_indexes:
        idx_name = idx["indexname"]
        idx_size = idx["index_size"]
        size_kb = idx_size / 1024

        if idx_name in KEEP_INDEXES:
            sql_parts.append(f"-- KEPT (safelist): {idx_name} ({size_kb:.0f} KB)")
            unused_kept_count += 1
            continue

        if idx_name in fk_index_names_to_create:
            sql_parts.append(f"-- KEPT (covers FK): {idx_name} ({size_kb:.0f} KB)")
            unused_kept_count += 1
            continue

        # Skip the duplicate index already handled in section 3
        if idx_name == "idx_docs_user_date":
            continue

        sql_parts.append(f"DROP INDEX IF EXISTS {idx_name};  -- {idx['tablename']} ({size_kb:.0f} KB)")
        unused_drop_count += 1

    sql_parts.append("")
    sql_parts.append(f"-- Total unused indexes dropped: {unused_drop_count}, kept: {unused_kept_count}")
    sql_parts.append("")

    # ----------------------------------------------------------------
    # Reload PostgREST schema cache and commit
    # ----------------------------------------------------------------
    sql_parts.append("-- =============================================================")
    sql_parts.append("-- Reload PostgREST schema cache")
    sql_parts.append("-- =============================================================")
    sql_parts.append("NOTIFY pgrst, 'reload schema';")
    sql_parts.append("")
    sql_parts.append("COMMIT;")

    # Output the SQL
    print("\n".join(sql_parts))

    # Summary to stderr
    print(f"\n-- SUMMARY:", file=sys.stderr)
    print(f"--   auth_rls_initplan policies fixed: {initplan_count}", file=sys.stderr)
    print(f"--   multiple_permissive rewritten: {multi_perm_count}", file=sys.stderr)
    print(f"--   redundant policies dropped: {dropped_redundant}", file=sys.stderr)
    print(f"--   duplicate indexes dropped: {'1' if 'idx_docs_user_date' in index_names else '0'}", file=sys.stderr)
    print(f"--   FK indexes created: {fk_index_count}", file=sys.stderr)
    print(f"--   unused indexes dropped: {unused_drop_count}", file=sys.stderr)
    print(f"--   unused indexes kept (safelist/FK): {unused_kept_count}", file=sys.stderr)


if __name__ == "__main__":
    main()
