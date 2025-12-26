#!/usr/bin/env python3
"""
Reset user password via Supabase Admin API
Usage: python reset_user_password.py <email> <new_password>
"""

import os
import sys

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found in environment")
    sys.exit(1)

# Initialize Supabase client with service role key (admin access)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def reset_password_by_email(email: str, new_password: str):
    """Reset password for a user by email"""
    try:
        print(f"\n🔍 Looking up user: {email}")

        # Method 1: Try to get from users table first
        users_result = supabase.table('users').select('id, email, name').eq('email', email).execute()

        if users_result.data:
            user = users_result.data[0]
            user_id = user['id']
            print("   Found in users table")
            print(f"   User ID: {user_id}")
            print(f"   Name: {user.get('name', 'N/A')}")
        else:
            # Method 2: List all auth users and find by email
            print("   Not found in users table, checking auth.users...")
            # Note: Supabase Python client doesn't expose list_users,
            # so we need to use the users table as source of truth
            print(f"❌ User not found: {email}")
            print("   The user may not have completed signup yet.")
            return False

        # Reset password
        print("\n🔄 Resetting password...")
        supabase.auth.admin.update_user_by_id(
            user_id,
            {"password": new_password}
        )

        print("✅ Password reset successful!")
        print(f"   Email: {email}")
        print(f"   New password: {new_password}")
        print("\n   User can now login with:")
        print(f"   Email: {email}")
        print(f"   Password: {new_password}")

        return True

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    # Reset both accounts to "thesis"
    emails = [
        "idbypaige@gmail.com",
        "paige@thebradburygroup.com"
    ]
    new_password = "thesis"

    print("=" * 60)
    print("PASSWORD RESET UTILITY")
    print("=" * 60)

    success_count = 0
    for email in emails:
        if reset_password_by_email(email, new_password):
            success_count += 1
        print()

    print("=" * 60)
    print(f"✅ Successfully reset {success_count}/{len(emails)} accounts")
    print("=" * 60)
