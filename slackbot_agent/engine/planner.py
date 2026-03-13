"""
Planner: determines how the query should be executed (first turn vs follow-up).
"""

from __future__ import annotations

from typing import Any

# Plan types matching PROJECT_CONTEXT: first query uses chat, subsequent use follow_up.
PLAN_CHAT = "chat"
PLAN_FOLLOW_UP = "follow_up"


def plan(question: str, conversation_context: list[dict[str, Any]] | None) -> str:
    """
    Decide execution mode from the question and prior context.
    Returns PLAN_CHAT for first query (no context), PLAN_FOLLOW_UP when context exists.
    """
    if not conversation_context or len(conversation_context) == 0:
        return PLAN_CHAT
    return PLAN_FOLLOW_UP
