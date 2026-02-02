"""Seed ADDIE-based Quick Prompts for Thesis L&D Users.

This script generates ADDIE workflow prompts for all existing users.
Run this once to populate the new ADDIE-categorized prompts.

Usage:
    python seed_addie_prompts.py
"""

import sys

from database import get_supabase
from logger_config import get_logger
from services.quick_prompt_generator import generate_addie_prompts, save_quick_prompts

logger = get_logger(__name__)
supabase = get_supabase()


def seed_addie_prompts_for_all_users():
    """Generate and save ADDIE prompts for all users in the system."""
    try:
        # Get all users
        logger.info("[Seed ADDIE Prompts] Fetching all users...")
        result = supabase.table("users").select("id, client_id, email").execute()
        users = result.data

        if not users:
            logger.warning("[Seed ADDIE Prompts] No users found in system")
            return

        logger.info(f"[Seed ADDIE Prompts] Found {len(users)} users")

        success_count = 0
        error_count = 0

        for user in users:
            user_id = user["id"]
            client_id = user.get("client_id")
            email = user.get("email", "unknown")

            try:
                # Check if user already has ADDIE prompts
                existing = (
                    supabase.table("user_quick_prompts")
                    .select("id")
                    .eq("user_id", user_id)
                    .eq("addie_phase", "Analysis")
                    .execute()
                )

                if existing.data and len(existing.data) > 0:
                    logger.info(
                        f"[Seed ADDIE Prompts] User {email} already has ADDIE prompts, skipping..."
                    )
                    continue

                logger.info(f"[Seed ADDIE Prompts] Generating prompts for user {email}...")

                # Generate ADDIE prompts (3 per phase)
                prompts = generate_addie_prompts(
                    user_id=user_id,
                    client_id=client_id,
                    phases=None,  # All phases
                    max_per_phase=3,
                )

                # Save to database
                save_result = save_quick_prompts(prompts)

                if save_result["success"]:
                    logger.info(
                        f"[Seed ADDIE Prompts] Successfully saved {save_result['count']} prompts for {email}"
                    )
                    success_count += 1
                else:
                    logger.error(
                        f"[Seed ADDIE Prompts] Failed to save prompts for {email}: {save_result.get('error')}"
                    )
                    error_count += 1

            except Exception as e:
                logger.error(f"[Seed ADDIE Prompts] Error processing user {email}: {e}")
                error_count += 1
                continue

        logger.info(
            f"[Seed ADDIE Prompts] Complete! Success: {success_count}, Errors: {error_count}"
        )

        return {
            "success": True,
            "users_processed": len(users),
            "success_count": success_count,
            "error_count": error_count,
        }

    except Exception as e:
        logger.error(f"[Seed ADDIE Prompts] Fatal error: {e}")
        return {"success": False, "error": str(e)}


def seed_addie_prompts_for_user(user_id: str):
    """Generate and save ADDIE prompts for a specific user.

    Args:
        user_id: User UUID
    """
    try:
        logger.info(f"[Seed ADDIE Prompts] Generating prompts for user {user_id}...")

        # Get user info
        user_result = (
            supabase.table("users").select("id, client_id, email").eq("id", user_id).execute()
        )

        if not user_result.data or len(user_result.data) == 0:
            logger.error(f"[Seed ADDIE Prompts] User {user_id} not found")
            return {"success": False, "error": "User not found"}

        user = user_result.data[0]
        client_id = user.get("client_id")

        # Generate ADDIE prompts
        prompts = generate_addie_prompts(
            user_id=user_id, client_id=client_id, phases=None, max_per_phase=3
        )

        # Save to database
        result = save_quick_prompts(prompts)

        if result["success"]:
            logger.info(f"[Seed ADDIE Prompts] Successfully saved {result['count']} prompts")
        else:
            logger.error(f"[Seed ADDIE Prompts] Failed to save prompts: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"[Seed ADDIE Prompts] Error: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Seed for specific user
        user_id = sys.argv[1]
        result = seed_addie_prompts_for_user(user_id)
    else:
        # Seed for all users
        result = seed_addie_prompts_for_all_users()

    if result["success"]:
        print("\n✅ Successfully seeded ADDIE prompts!")
        if "users_processed" in result:
            print(f"   Users processed: {result['users_processed']}")
            print(f"   Success: {result['success_count']}")
            print(f"   Errors: {result['error_count']}")
    else:
        print(f"\n❌ Failed to seed ADDIE prompts: {result.get('error')}")
        sys.exit(1)
