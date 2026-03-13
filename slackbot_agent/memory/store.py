"""In-memory conversation store for Slack channels."""

from collections import deque
from typing import Any

MAX_TURNS = 10

_store: dict[str, deque[dict[str, str]]] = {}


def get_context(channel_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """
    Return the last `limit` conversation turns for the channel.

    Each turn is {"user": str, "assistant": str}. Order is oldest first
    (chronological), so the most recent turn is last in the list.
    Returns [] if the channel has no history or channel_id is empty.
    """
    if not channel_id:
        return []
    q = _store.get(channel_id)
    if not q:
        return []
    items = list(q)
    return items[-limit:] if limit < len(items) else items.copy()


def append(channel_id: str, user_text: str, assistant_text: str) -> None:
    """
    Append one conversation turn for the channel.

    Storage is bounded to MAX_TURNS per channel; older turns are dropped.
    No-op if channel_id is empty.
    """
    if not channel_id:
        return
    if channel_id not in _store:
        _store[channel_id] = deque(maxlen=MAX_TURNS)
    _store[channel_id].append({"user": user_text, "assistant": assistant_text})
