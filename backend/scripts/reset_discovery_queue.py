"""Reset discovery queue - clear candidates and reset scan flags for re-scanning."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_supabase

def reset_discovery_queue():
    supabase = get_supabase()
    
    print("Clearing pending candidates...")
    
    # Clear task candidates
    result = supabase.table('task_candidates').delete().eq('status', 'pending').execute()
    print(f"  - Deleted {len(result.data)} task candidates")
    
    # Clear opportunity candidates
    result = supabase.table('project_candidates').delete().eq('status', 'pending').execute()
    print(f"  - Deleted {len(result.data)} opportunity candidates")
    
    # Clear stakeholder candidates
    result = supabase.table('stakeholder_candidates').delete().eq('status', 'pending').execute()
    print(f"  - Deleted {len(result.data)} stakeholder candidates")
    
    print("\nResetting scan flags on Granola documents...")
    
    # Reset granola_scanned_at using RPC to handle ILIKE properly
    result = supabase.rpc('reset_granola_scan_flags', {}).execute()
    print(f"  - Reset granola_scanned_at on documents")
    
    print("\nDone! Now trigger the Granola scan to re-process documents.")

if __name__ == '__main__':
    reset_discovery_queue()
