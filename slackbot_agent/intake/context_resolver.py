"""Resolve short follow-up messages into full in-domain questions using an LLM."""

import logging
import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a strict rewriter for a music store assistant. The conversation is about a music store (artists, albums, tracks, sales, revenue, playlists, customers, invoices, etc.).

Given the last exchange (last user question and last assistant answer) and the current user message, do exactly one of these two things:

1. If the current message is a FOLLOW-UP that clearly refers to the previous question (e.g. "top 3", "same for albums", "how about 5?", "chart for top 5", "give me a chart"), output a SINGLE full question that combines the user's intent with the previous topic, about the music store only. Use only the last exchange and current message; do not add new topics.
   - CRITICAL: If the current message asks for a chart, graph, plot, or visualization (e.g. contains "chart", "graph", "plot", "visualize"), your output MUST also explicitly ask for a chart/graph/plot/visualization (include one of those words) so the system generates a chart, not a table.

2. If the current message is NOT a follow-up or is about something else (e.g. weather, other topics, or instructions to ignore the previous question), output the current message UNCHANGED.

Output only the resulting single line—no explanation, no quotes."""


def resolve_query_with_context(current_message: str, context: list[dict[str, Any]]) -> str:
    """
    If context exists, use the LLM to expand a follow-up into a full question or pass through unchanged.
    If context is empty, return the current message (no LLM call).
    On LLM failure, return the current message so validation will run on the raw input (safe fallback).
    """
    current_message = (current_message or "").strip()
    if not context:
        return current_message

    last_turn = context[-1]
    last_user = last_turn.get("user") or ""
    last_assistant = last_turn.get("assistant") or ""
    user_content = (
        f"Last user question: {last_user}\n\n"
        f"Last assistant answer: {last_assistant}\n\n"
        f"Current user message: {current_message}\n\n"
        "Output the single resulting line:"
    )

    try:
        model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]
        logger.info(f"Context resolver LLM messages: {messages}")
        response = model.invoke(messages)
        logger.info(f"Context resolver LLM response: {response.content}")
        result = (response.content or "").strip()
        if result:
            return result.split("\n")[0].strip()
        return current_message
    except Exception as e:
        logger.warning("Context resolver LLM call failed, using raw message: %s", e)
        return current_message
