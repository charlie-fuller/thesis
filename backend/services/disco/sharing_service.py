"""
PuRDy Sharing Service

Handles initiative sharing and permissions management.
"""

import asyncio
from typing import Dict, List, Optional
from uuid import uuid4

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)
supabase = get_supabase()

# Valid roles
VALID_ROLES = {'owner', 'editor', 'viewer'}


async def add_member(
    initiative_id: str,
    user_email: str,
    role: str,
    inviter_id: str
) -> Dict:
    """
    Add a member to an initiative by email.

    Args:
        initiative_id: Initiative UUID
        user_email: Email of user to invite
        role: Role to assign (editor, viewer)
        inviter_id: ID of user sending the invite

    Returns:
        Created member record
    """
    logger.info(f"Adding member {user_email} to initiative {initiative_id} as {role}")

    if role not in VALID_ROLES or role == 'owner':
        raise ValueError(f"Invalid role: {role}. Must be 'editor' or 'viewer'")

    # Check inviter is owner or editor
    inviter_role = await get_member_role(initiative_id, inviter_id)
    if inviter_role not in ('owner', 'editor'):
        raise PermissionError("Only owners and editors can invite members")

    try:
        # Find user by email
        user_result = await asyncio.to_thread(
            lambda: supabase.table('users')
                .select('id, email, name')
                .eq('email', user_email)
                .single()
                .execute()
        )

        if not user_result.data:
            raise ValueError(f"User not found: {user_email}")

        user = user_result.data
        user_id = user['id']

        # Check if already a member
        existing = await asyncio.to_thread(
            lambda: supabase.table('disco_initiative_members')
                .select('id, role')
                .eq('initiative_id', initiative_id)
                .eq('user_id', user_id)
                .execute()
        )

        if existing.data:
            # Update existing membership
            result = await asyncio.to_thread(
                lambda: supabase.table('disco_initiative_members')
                    .update({'role': role})
                    .eq('initiative_id', initiative_id)
                    .eq('user_id', user_id)
                    .execute()
            )
            member = result.data[0]
            member['user'] = user
            logger.info(f"Updated member role for {user_email}")
            return member

        # Add new member
        member_id = str(uuid4())
        result = await asyncio.to_thread(
            lambda: supabase.table('disco_initiative_members').insert({
                'id': member_id,
                'initiative_id': initiative_id,
                'user_id': user_id,
                'role': role
            }).execute()
        )

        member = result.data[0]
        member['user'] = user
        logger.info(f"Added member {user_email} to initiative")
        return member

    except Exception as e:
        logger.error(f"Error adding member: {e}")
        raise


async def remove_member(
    initiative_id: str,
    user_id: str,
    remover_id: str
) -> bool:
    """
    Remove a member from an initiative.

    Args:
        initiative_id: Initiative UUID
        user_id: ID of user to remove
        remover_id: ID of user performing removal

    Returns:
        True if removed successfully
    """
    logger.info(f"Removing member {user_id} from initiative {initiative_id}")

    # Check remover permission
    remover_role = await get_member_role(initiative_id, remover_id)
    if remover_role != 'owner':
        raise PermissionError("Only owners can remove members")

    # Check target member role
    target_role = await get_member_role(initiative_id, user_id)
    if target_role == 'owner':
        raise ValueError("Cannot remove the owner")

    if not target_role:
        raise ValueError(f"User {user_id} is not a member of this initiative")

    try:
        await asyncio.to_thread(
            lambda: supabase.table('disco_initiative_members')
                .delete()
                .eq('initiative_id', initiative_id)
                .eq('user_id', user_id)
                .execute()
        )

        logger.info(f"Removed member {user_id} from initiative")
        return True

    except Exception as e:
        logger.error(f"Error removing member: {e}")
        raise


async def list_members(initiative_id: str) -> List[Dict]:
    """
    List all members of an initiative.

    Args:
        initiative_id: Initiative UUID

    Returns:
        List of member records with user info
    """
    logger.info(f"Listing members for initiative {initiative_id}")

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('disco_initiative_members')
                .select('*, users!disco_initiative_members_user_id_fkey(id, email, name)')
                .eq('initiative_id', initiative_id)
                .order('invited_at')
                .execute()
        )

        members = result.data or []

        # Flatten user data
        for member in members:
            if member.get('users'):
                member['user'] = member['users']
                del member['users']

        return members

    except Exception as e:
        logger.error(f"Error listing members: {e}")
        raise


async def update_member_role(
    initiative_id: str,
    user_id: str,
    new_role: str,
    updater_id: str
) -> Dict:
    """
    Update a member's role.

    Args:
        initiative_id: Initiative UUID
        user_id: ID of member to update
        new_role: New role to assign
        updater_id: ID of user making the update

    Returns:
        Updated member record
    """
    logger.info(f"Updating role for {user_id} to {new_role}")

    if new_role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {new_role}")

    # Check updater permission
    updater_role = await get_member_role(initiative_id, updater_id)
    if updater_role != 'owner':
        raise PermissionError("Only owners can change roles")

    # Check target member exists
    target_role = await get_member_role(initiative_id, user_id)
    if not target_role:
        raise ValueError(f"User {user_id} is not a member")

    # Cannot change owner role
    if target_role == 'owner' and new_role != 'owner':
        raise ValueError("Cannot change owner's role")

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('disco_initiative_members')
                .update({'role': new_role})
                .eq('initiative_id', initiative_id)
                .eq('user_id', user_id)
                .execute()
        )

        logger.info(f"Updated role for {user_id} to {new_role}")
        return result.data[0] if result.data else {}

    except Exception as e:
        logger.error(f"Error updating member role: {e}")
        raise


async def get_member_role(initiative_id: str, user_id: str) -> Optional[str]:
    """
    Get a user's role in an initiative.

    Args:
        initiative_id: Initiative UUID
        user_id: User's ID

    Returns:
        Role string or None if not a member
    """
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('disco_initiative_members')
                .select('role')
                .eq('initiative_id', initiative_id)
                .eq('user_id', user_id)
                .single()
                .execute()
        )

        return result.data.get('role') if result.data else None

    except Exception:
        return None


async def check_permission(
    initiative_id: str,
    user_id: str,
    required_role: str = 'viewer'
) -> bool:
    """
    Check if user has at least the required role.

    Args:
        initiative_id: Initiative UUID
        user_id: User's ID
        required_role: Minimum required role (viewer, editor, owner)

    Returns:
        True if user has sufficient permission
    """
    role_hierarchy = {'viewer': 1, 'editor': 2, 'owner': 3}

    user_role = await get_member_role(initiative_id, user_id)
    if not user_role:
        return False

    required_level = role_hierarchy.get(required_role, 1)
    user_level = role_hierarchy.get(user_role, 0)

    return user_level >= required_level


async def transfer_ownership(
    initiative_id: str,
    new_owner_id: str,
    current_owner_id: str
) -> bool:
    """
    Transfer ownership of an initiative.

    Args:
        initiative_id: Initiative UUID
        new_owner_id: ID of new owner
        current_owner_id: ID of current owner

    Returns:
        True if transferred successfully
    """
    logger.info(f"Transferring ownership of {initiative_id} to {new_owner_id}")

    # Verify current owner
    current_role = await get_member_role(initiative_id, current_owner_id)
    if current_role != 'owner':
        raise PermissionError("Only the current owner can transfer ownership")

    # Verify new owner is a member
    new_owner_role = await get_member_role(initiative_id, new_owner_id)
    if not new_owner_role:
        raise ValueError("New owner must already be a member of the initiative")

    try:
        # Update new owner
        await asyncio.to_thread(
            lambda: supabase.table('disco_initiative_members')
                .update({'role': 'owner'})
                .eq('initiative_id', initiative_id)
                .eq('user_id', new_owner_id)
                .execute()
        )

        # Demote current owner to editor
        await asyncio.to_thread(
            lambda: supabase.table('disco_initiative_members')
                .update({'role': 'editor'})
                .eq('initiative_id', initiative_id)
                .eq('user_id', current_owner_id)
                .execute()
        )

        # Update initiative created_by
        await asyncio.to_thread(
            lambda: supabase.table('disco_initiatives')
                .update({'created_by': new_owner_id})
                .eq('id', initiative_id)
                .execute()
        )

        logger.info(f"Transferred ownership to {new_owner_id}")
        return True

    except Exception as e:
        logger.error(f"Error transferring ownership: {e}")
        raise
