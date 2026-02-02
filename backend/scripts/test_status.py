#!/usr/bin/env python3
"""Test the get_scan_status function directly."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from database import get_supabase
from services.granola_scanner import DEFAULT_SINCE_DATE, get_document_meeting_date, get_scan_status

print(f"DEFAULT_SINCE_DATE: {DEFAULT_SINCE_DATE}")

# Get a real user_id from the database
supabase = get_supabase()
users = supabase.table("users").select("id").limit(1).execute()
if users.data:
    user_id = users.data[0]["id"]
    print(f"Testing with user_id: {user_id}")

    # Call get_scan_status
    status = get_scan_status(user_id)
    print("\nStatus result:")
    for k, v in status.items():
        print(f"  {k}: {v}")
else:
    print("No users found")

# Also test get_document_meeting_date directly
print("\n\nTesting get_document_meeting_date on sample docs:")
docs = (
    supabase.table("documents")
    .select("id, filename, original_date, obsidian_file_path")
    .limit(5)
    .execute()
)

for doc in docs.data or []:
    meeting_date = get_document_meeting_date(doc)
    print(
        f"  {doc.get('filename', 'Unknown')[:40]}: original_date={doc.get('original_date')}, parsed={meeting_date}"
    )
