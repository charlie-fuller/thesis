"""
Instruction Loader Service

Loads agent system instructions from XML files.
XML files in backend/system_instructions/agents/ are the SINGLE SOURCE OF TRUTH.

When instructions are updated:
1. XML files are the authoritative source
2. On save in admin UI, create a new version in agent_instruction_versions
3. Running agents hot-reload from the active version in DB
"""

import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Base path for instruction files
INSTRUCTIONS_DIR = Path(__file__).parent.parent / "system_instructions" / "agents"


def get_instruction_file_path(agent_name: str) -> Path:
    """Get the path to an agent's XML instruction file."""
    return INSTRUCTIONS_DIR / f"{agent_name.lower()}.xml"


def load_instruction_from_file(agent_name: str) -> Optional[str]:
    """
    Load an agent's system instruction from its XML file.

    Args:
        agent_name: The agent's name (e.g., "atlas", "fortuna")

    Returns:
        The instruction content as a string, or None if file doesn't exist.
    """
    file_path = get_instruction_file_path(agent_name)

    if not file_path.exists():
        logger.warning(f"No instruction file found for agent {agent_name} at {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.info(f"Loaded instruction for {agent_name} from {file_path} ({len(content)} chars)")
        return content
    except Exception as e:
        logger.error(f"Failed to load instruction for {agent_name}: {e}")
        return None


def save_instruction_to_file(agent_name: str, content: str) -> bool:
    """
    Save an agent's system instruction to its XML file.

    Args:
        agent_name: The agent's name
        content: The instruction content

    Returns:
        True if saved successfully, False otherwise.
    """
    file_path = get_instruction_file_path(agent_name)

    try:
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Saved instruction for {agent_name} to {file_path} ({len(content)} chars)")
        return True
    except Exception as e:
        logger.error(f"Failed to save instruction for {agent_name}: {e}")
        return False


def get_instruction_file_mtime(agent_name: str) -> Optional[datetime]:
    """Get the modification time of an agent's instruction file."""
    file_path = get_instruction_file_path(agent_name)

    if not file_path.exists():
        return None

    try:
        mtime = file_path.stat().st_mtime
        return datetime.fromtimestamp(mtime)
    except Exception as e:
        logger.error(f"Failed to get mtime for {agent_name}: {e}")
        return None


def list_available_instruction_files() -> list[dict]:
    """
    List all available instruction XML files.

    Returns:
        List of dicts with agent_name, file_path, size, and modified_at.
    """
    if not INSTRUCTIONS_DIR.exists():
        logger.warning(f"Instructions directory does not exist: {INSTRUCTIONS_DIR}")
        return []

    files = []
    for file_path in INSTRUCTIONS_DIR.glob("*.xml"):
        try:
            stat = file_path.stat()
            files.append({
                "agent_name": file_path.stem,
                "file_path": str(file_path),
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        except Exception as e:
            logger.error(f"Failed to stat {file_path}: {e}")

    return sorted(files, key=lambda x: x["agent_name"])


def instruction_file_exists(agent_name: str) -> bool:
    """Check if an instruction file exists for an agent."""
    return get_instruction_file_path(agent_name).exists()
