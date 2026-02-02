"""Services module for Thesis
Contains business logic and external API integrations
"""

# Lazy imports to avoid import chain issues with optional dependencies (llama_index)
# This allows tests to run without requiring all dependencies


def start_scheduler():
    """Lazy import for sync scheduler start."""
    from .sync_scheduler import start_scheduler as _start

    return _start()


def stop_scheduler():
    """Lazy import for sync scheduler stop."""
    from .sync_scheduler import stop_scheduler as _stop

    return _stop()


# Direct import for lightweight services without heavy dependencies
from .useable_output_detector import process_conversation_for_useable_output

__all__ = [
    "process_conversation_for_useable_output",
    "start_scheduler",
    "stop_scheduler",
]
