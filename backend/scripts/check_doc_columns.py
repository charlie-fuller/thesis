#!/usr/bin/env python3
"""Check what columns are available on documents table."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from database import get_supabase

supabase = get_supabase()

# Get one document to see all columns
result = supabase.table("documents").select("*").limit(1).execute()

if result.data:
    doc = result.data[0]
    print("Available columns on documents table:")
    print("-" * 50)
    for key, value in sorted(doc.items()):
        val_preview = str(value)[:50] if value else "NULL"
        print(f"  {key}: {val_preview}")
else:
    print("No documents found")
