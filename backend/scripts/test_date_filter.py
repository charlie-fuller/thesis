#!/usr/bin/env python3
"""Test what the RPC function returns."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from database import get_supabase

supabase = get_supabase()

# Check what RPC returns
result = supabase.rpc('get_granola_documents_to_scan', {
    'p_user_id': '00000000-0000-0000-0000-000000000000',  # dummy
    'p_force_rescan': True
}).execute()

print(f"RPC returned {len(result.data or [])} documents")

if result.data:
    print("\nSample document columns:")
    doc = result.data[0]
    for key in sorted(doc.keys()):
        val = str(doc[key])[:50] if doc[key] else 'NULL'
        print(f"  {key}: {val}")
else:
    print("No documents returned by RPC")
    print("\nTrying direct query...")
    
    # Fall back to direct query
    result = supabase.table('documents') \
        .select('id, filename, original_date, granola_scanned_at, obsidian_file_path') \
        .limit(5) \
        .execute()
    
    print(f"Direct query returned {len(result.data or [])} documents")
    if result.data:
        doc = result.data[0]
        for key in sorted(doc.keys()):
            val = str(doc[key])[:50] if doc[key] else 'NULL'
            print(f"  {key}: {val}")
