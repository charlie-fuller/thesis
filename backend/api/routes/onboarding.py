"""
Onboarding routes
Handles user onboarding status and preferences
"""
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])
supabase = get_supabase()


# ============================================================================
# Request/Response Models
# ============================================================================

class OnboardingPreferences(BaseModel):
    notifications_enabled: Optional[bool] = True
    email_digest: Optional[bool] = False


class CompleteOnboardingRequest(BaseModel):
    preferences: Optional[OnboardingPreferences] = None


class OnboardingStatusResponse(BaseModel):
    success: bool
    onboarded: bool
    preferences: Optional[dict] = None


# ============================================================================
# Onboarding Status Routes
# ============================================================================

@router.get("/status")
async def get_onboarding_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the current user's onboarding status.
    Returns whether they've completed onboarding and their preferences.
    """
    try:
        user_id = current_user['id']

        # Query user's onboarding status
        result = await asyncio.to_thread(
            lambda: supabase.table('users')\
                .select('onboarded, onboarding_preferences, onboarded_at')\
                .eq('id', user_id)\
                .single()\
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        onboarded = result.data.get('onboarded', False)
        preferences = result.data.get('onboarding_preferences', {})
        onboarded_at = result.data.get('onboarded_at')

        return {
            'success': True,
            'onboarded': onboarded,
            'preferences': preferences,
            'onboarded_at': onboarded_at
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching onboarding status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete")
async def complete_onboarding(
    request: CompleteOnboardingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Mark onboarding as complete and save user preferences.
    """
    try:
        user_id = current_user['id']

        # Prepare update data
        update_data = {
            'onboarded': True,
            'onboarded_at': 'now()'
        }

        # Add preferences if provided
        if request.preferences:
            update_data['onboarding_preferences'] = {
                'notifications_enabled': request.preferences.notifications_enabled,
                'email_digest': request.preferences.email_digest
            }

        # Update user record
        result = await asyncio.to_thread(
            lambda: supabase.table('users')\
                .update(update_data)\
                .eq('id', user_id)\
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"✅ User {user_id} completed onboarding")

        return {
            'success': True,
            'message': 'Onboarding completed successfully',
            'preferences': update_data.get('onboarding_preferences', {})
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error completing onboarding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skip")
async def skip_onboarding(
    current_user: dict = Depends(get_current_user)
):
    """
    Skip onboarding (mark as complete but without preferences).
    For experienced users who don't need the tour.
    """
    try:
        user_id = current_user['id']

        # Mark as onboarded with default preferences
        update_data = {
            'onboarded': True,
            'onboarded_at': 'now()',
            'onboarding_preferences': {
                'notifications_enabled': True,
                'email_digest': False,
                'skipped': True
            }
        }

        result = await asyncio.to_thread(
            lambda: supabase.table('users')\
                .update(update_data)\
                .eq('id', user_id)\
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"✅ User {user_id} skipped onboarding")

        return {
            'success': True,
            'message': 'Onboarding skipped successfully'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error skipping onboarding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences")
async def update_onboarding_preferences(
    preferences: OnboardingPreferences,
    current_user: dict = Depends(get_current_user)
):
    """
    Update onboarding preferences (can be called anytime after onboarding).
    """
    try:
        user_id = current_user['id']

        # Update preferences
        update_data = {
            'onboarding_preferences': {
                'notifications_enabled': preferences.notifications_enabled,
                'email_digest': preferences.email_digest
            }
        }

        result = await asyncio.to_thread(
            lambda: supabase.table('users')\
                .update(update_data)\
                .eq('id', user_id)\
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"✅ Updated onboarding preferences for user {user_id}")

        return {
            'success': True,
            'message': 'Preferences updated successfully',
            'preferences': update_data['onboarding_preferences']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_onboarding(
    current_user: dict = Depends(get_current_user)
):
    """
    Reset onboarding status (allows user to see the tour again).
    """
    try:
        user_id = current_user['id']

        # Reset onboarding status
        update_data = {
            'onboarded': False,
            'onboarded_at': None
        }

        result = await asyncio.to_thread(
            lambda: supabase.table('users')\
                .update(update_data)\
                .eq('id', user_id)\
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"✅ Reset onboarding for user {user_id}")

        return {
            'success': True,
            'message': 'Onboarding reset successfully. You will see the welcome tour on next login.'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error resetting onboarding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
