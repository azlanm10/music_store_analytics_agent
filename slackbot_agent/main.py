"""
Slack bot entry point: Bolt app, message handler, and flow (intake → engine → output → memory).
"""

import logging
import os
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from slackbot_agent.engine import get_agent, run_query
from slackbot_agent.intake.context_resolver import resolve_query_with_context
from slackbot_agent.output import send_to_slack
from slackbot_agent.intake.guardrails import check_pii, check_blocked
from slackbot_agent.intake.help import GREETING_RESPONSE, HELP_RESPONSE, is_greeting, is_help_request
from slackbot_agent.intake.validator import has_music_keywords, validate_query
from slackbot_agent.memory import append as memory_append, get_context as memory_get_context


load_dotenv()

LOG_FILE = os.getenv("LOG_FILE")
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
    force=True,  # Apply our config even if root logger already had handlers (e.g. from imports)
)
logger = logging.getLogger(__name__)

app = App(token=os.getenv("SLACK_BOT_TOKEN"))


def _get_message_text(body: dict) -> str:
    """Extract user message text from Slack event body."""
    return (body.get("event") or {}).get("text") or ""


def _get_channel_and_user(body: dict) -> tuple[str, str]:
    """Extract channel_id and user_id from Slack event body."""
    event = body.get("event") or {}
    return event.get("channel") or "", event.get("user") or ""


@app.message("")
def handle_message_events(body, say, client):
    logger.info(f"Handling message events: {body}")
    text = _get_message_text(body)
    channel_id, _user_id = _get_channel_and_user(body)
    if not text.strip():
        say("Hello, how can I help you today?")
        return

    if is_greeting(text):
        say(GREETING_RESPONSE)
        return

    if is_help_request(text):
        say(HELP_RESPONSE)
        return

    # Memory: load context before validation for follow-up resolution
    context = memory_get_context(channel_id, limit=10) if channel_id else []

    # Compute effective query: use LLM to expand follow-ups when no keywords but we have context
    if has_music_keywords(text):
        effective_query = text
    elif context:
        effective_query = resolve_query_with_context(text, context)
    else:
        effective_query = text

    # Invoke: Validator — ensure request is in music-store domain
    validation = validate_query(effective_query)
    if not validation["passed"]:
        say(validation["message"])
        return

    query = validation["query"]

    # Invoke: Guardrails — PII and read-only / prompt-injection safety
    if check_pii(query):
        say("I can't process requests that ask for or expose personal information.")
        return
    if check_blocked(query):
        say("I can only answer read-only questions about the music store. I can't run changes or follow other instructions.")
        return

    # Context already loaded above for effective-query resolution; reuse for Engine

    # Engine returns either plain text or CHART_BASE64:...; response builder uploads images or sends text
    response_text = run_query(query, conversation_context=context)
    send_to_slack(response_text, client=client, channel_id=channel_id, say=say)
    if channel_id:
        memory_append(channel_id, query, response_text)

def main():
    try:
        # Ensure chart dir exists so PandasAI's plt.savefig("exports/charts/...") succeeds
        (Path(__file__).resolve().parent / "exports" / "charts").mkdir(parents=True, exist_ok=True)
        # Optional: init agent once at startup so first message doesn't pay load/build cost
        get_agent()
        handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
        handler.start()
        logger.info("⚡ Slack bot is running! ⚡")
    except Exception as e:
        logger.error(f"Error starting Slack bot: {e}")

if __name__ == "__main__":
    main()

