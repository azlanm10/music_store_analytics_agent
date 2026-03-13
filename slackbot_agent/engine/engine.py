"""
Engine: public API. Delegates to Orchestrator and Reasoner (see PROJECT_CONTEXT).
"""

from __future__ import annotations

from pandasai import Agent

from slackbot_agent.engine.orchestrator import run
from slackbot_agent.engine.reasoner import get_agent as _get_agent


def get_agent() -> Agent:
    """Return the singleton PandasAI Agent (used for optional startup init)."""
    return _get_agent()


def run_query(question: str, conversation_context: list[dict[str, str]] | None = None) -> str:
    """Execute the user question via Planner + Reasoner (Orchestrator)."""
    return run(question, conversation_context)
