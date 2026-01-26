#!/usr/bin/env python3
"""
One-time script to reset user passwords and set roles to admin.
Run with: python scripts/reset_user_passwords.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.credentials import get_credentials

from supabase import create_client

creds = get_credentials()
SUPABASE_URL = creds['supabase_url']
SUPABASE_SERVICE_ROLE_KEY = creds['supabase_key']

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Users to update
USERS = [
    "aparnam.sai@gmail.com",
    "teresa.waggoner.id@gmail.com"
]

NEW_PASSWORD = "thesis"

def main():
    for email in USERS:
        print(f"\n📧 Processing: {email}")

        # Get user ID from auth.users
        try:
            # List users and find by email
            users_response = supabase.auth.admin.list_users()
            user = None
            for u in users_response:
                if hasattr(u, 'email') and u.email == email:
                    user = u
                    break

            if not user:
                print(f"  ⚠️  User not found in auth: {email}")
                continue

            user_id = user.id
            print(f"  Found user ID: {user_id}")

            # Update password
            supabase.auth.admin.update_user_by_id(
                user_id,
                {"password": NEW_PASSWORD}
            )
            print(f"  ✅ Password reset to '{NEW_PASSWORD}'")

            # Update role to admin in users table
            result = supabase.table('users').update({"role": "admin"}).eq('email', email).execute()
            if result.data:
                print("  ✅ Role set to 'admin'")
            else:
                print("  ⚠️  User not found in users table, creating...")
                supabase.table('users').upsert({
                    "id": user_id,
                    "email": email,
                    "role": "admin"
                }).execute()
                print("  ✅ User created with admin role")

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

    print("\n✅ Done!")

if __name__ == "__main__":
    main()
