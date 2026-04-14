"""Repository for meeting-related collections.

Collections: meeting_rooms, meeting_room_messages, meeting_room_participants,
meeting_transcripts.
"""

import pb_client as pb


# ---------------------------------------------------------------------------
# meeting_rooms
# ---------------------------------------------------------------------------

def list_meeting_rooms(*, status: str = "", sort: str = "-updated") -> list[dict]:
    parts = []
    if status:
        parts.append(f"status='{pb.escape_filter(status)}'")
    return pb.get_all("meeting_rooms", filter=" && ".join(parts), sort=sort)


def get_meeting_room(room_id: str) -> dict | None:
    return pb.get_record("meeting_rooms", room_id)


def create_meeting_room(data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("user_id", None)
    return pb.create_record("meeting_rooms", data)


def update_meeting_room(room_id: str, data: dict) -> dict:
    return pb.update_record("meeting_rooms", room_id, data)


def delete_meeting_room(room_id: str) -> None:
    pb.delete_record("meeting_rooms", room_id)


# ---------------------------------------------------------------------------
# meeting_room_messages
# ---------------------------------------------------------------------------

def get_room_messages(room_id: str, *, since_turn: int = 0) -> list[dict]:
    """Get messages for a meeting room, optionally filtered by turn number."""
    esc = pb.escape_filter(room_id)
    if since_turn > 0:
        filter_str = f"room_id='{esc}' && turn_number>{since_turn}"
    else:
        filter_str = f"room_id='{esc}'"
    return pb.get_all("meeting_room_messages", filter=filter_str, sort="created")


def get_room_message(message_id: str) -> dict | None:
    return pb.get_record("meeting_room_messages", message_id)


def create_room_message(data: dict) -> dict:
    return pb.create_record("meeting_room_messages", data)


def update_room_message(message_id: str, data: dict) -> dict:
    return pb.update_record("meeting_room_messages", message_id, data)


def delete_room_message(message_id: str) -> None:
    pb.delete_record("meeting_room_messages", message_id)


# ---------------------------------------------------------------------------
# meeting_room_participants
# ---------------------------------------------------------------------------

def get_room_participants(room_id: str) -> list[dict]:
    return pb.get_all(
        "meeting_room_participants",
        filter=f"room_id='{pb.escape_filter(room_id)}'",
        sort="created",
    )


def add_room_participant(data: dict) -> dict:
    return pb.create_record("meeting_room_participants", data)


def remove_room_participant(participant_id: str) -> None:
    pb.delete_record("meeting_room_participants", participant_id)


# ---------------------------------------------------------------------------
# meeting_transcripts
# ---------------------------------------------------------------------------

def list_meeting_transcripts(*, room_id: str = "", sort: str = "-created") -> list[dict]:
    parts = []
    if room_id:
        parts.append(f"room_id='{pb.escape_filter(room_id)}'")
    return pb.get_all("meeting_transcripts", filter=" && ".join(parts), sort=sort)


def get_meeting_transcript(transcript_id: str) -> dict | None:
    return pb.get_record("meeting_transcripts", transcript_id)


def create_meeting_transcript(data: dict) -> dict:
    return pb.create_record("meeting_transcripts", data)


def update_meeting_transcript(transcript_id: str, data: dict) -> dict:
    return pb.update_record("meeting_transcripts", transcript_id, data)


def delete_meeting_transcript(transcript_id: str) -> None:
    pb.delete_record("meeting_transcripts", transcript_id)
