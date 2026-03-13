"""
PandasAI Reasoner: generates SQL with the Semantic Layer and executes against Chinook.
"""

from __future__ import annotations

import logging
import os

import pandasai as pai
from pandasai import Agent

from slackbot_agent.semantic_layer import load_sources

logger = logging.getLogger(__name__)

try:
    from pandasai_litellm.litellm import LiteLLM
except ImportError:
    LiteLLM = None  # type: ignore[misc, assignment]

# Placeholder; update with your full system prompt.
PROMPT = """
# Role
You are an expert SQL analyst and PostgreSQL database specialist.

# CRITICAL — which query to answer
The prompt may contain multiple ### QUERY lines (conversation history). You MUST answer ONLY the LAST (most recent) query. Ignore earlier queries when deciding what to return. Do not return a chart just because an earlier query in the thread asked for a chart.

# Task
Answer the last user question about the Chinook music store using the available semantic layer (tables and views).
Generate correct, read-only SQL and return a clear, conversational summary of the results.

# SQL: when to use LIMIT
- Add LIMIT only when the user explicitly asks for a specific number (e.g. "top 5", "top 10", "first 3", "top 5 artists"). 
- When the user asks for "artists with most albums", "which artists have the most albums", "revenue per artist", or similar without a number, do NOT add LIMIT—return all rows ordered appropriately (e.g. ORDER BY album_count DESC or ORDER BY revenue DESC).

# Output format
-  If the LAST query contains "chart", "graph", "visualize", or "plot" (e.g. "what is the chart for the top 5 artists with the most albums?", "give me a chart for top 5"), you MUST return a CHART: run your SQL, build a matplotlib figure (e.g. plt.bar or plt.barh), save with plt.savefig to a path under exports/charts/ (e.g. "exports/charts/temp_chart.png"), then result = {"type": "plot", "value": that_path}. Do NOT return type "dataframe" or "string" for chart requests.
-  use dataframe if the user ask for the whole data without any limit or specific number.
- Return a string if the user ask for a total numer or top N number of something.
"""

_agent: Agent | None = None


def _configure_llm() -> None:
    if LiteLLM is None:
        return
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    api_key = os.getenv("OPENAI_API_KEY", "")
    pai.config.set({"llm": LiteLLM(model=model, api_key=api_key)})


def get_agent() -> Agent:
    """Return the singleton PandasAI Agent. Sources (from pai.load or local schema.yaml) are passed to the Agent."""
    global _agent
    if _agent is not None:
        return _agent
    _configure_llm()
    sources = load_sources()  # list of datasets from platform or pai.create from YAML
    logger.info(sources)
    _agent = Agent(sources, description=PROMPT) if PROMPT.strip() else Agent(sources)
    logger.info(_agent)
    return _agent


def chat(agent: Agent, question: str) -> str:
    """First-turn: Agent.chat(question). Returns raw response; response builder normalizes chart path."""
    logger.info("Calling agent.chat with question: %s", question)
    response = agent.chat(question)
    return str(response)


def follow_up(agent: Agent, question: str) -> str:
    """Subsequent turn: Agent.follow_up(question). Returns raw response; response builder normalizes chart path."""
    logger.info("Calling agent.follow_up with question: %s", question)
    response = agent.follow_up(question)
    return str(response)
