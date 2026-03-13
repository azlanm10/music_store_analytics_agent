"""
Orchestrator: manages workflow and coordination (Planner + PandasAI Reasoner).
"""

from __future__ import annotations

from slackbot_agent.engine.planner import PLAN_CHAT, plan
from slackbot_agent.engine.reasoner import chat, follow_up, get_agent


def run(question: str, conversation_context: list[dict[str, str]] | None = None) -> str:
    """
    Run the engine: plan how to execute, then call the reasoner (chat or follow_up).
    """
    agent = get_agent()
    execution = plan(question, conversation_context)
    if execution == PLAN_CHAT:
        return chat(agent, question)
    return follow_up(agent, question)
