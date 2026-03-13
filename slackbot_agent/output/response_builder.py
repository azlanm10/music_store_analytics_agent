"""
Response builder: format engine output for Slack and send it (text or image upload).

- Chart response: when engine returns a chart file path, normalizes to CHART_BASE64 (read file → base64) and uploads to Slack. Also accepts CHART_BASE64:... directly.
- Converts tabular data into a table for Slack.
- Truncate very long replies and ensure messages stay within Slack limits.
"""

from __future__ import annotations

import base64
import io
import logging
import re
from pathlib import Path

# Slack message text limit (conservative for a single message)
MAX_SLACK_MESSAGE_LENGTH = 4000

logger = logging.getLogger(__name__)


def _normalize_chart_response(raw: str) -> str:
    """When engine returns a chart file path, read the file and return CHART_BASE64. Otherwise return unchanged (e.g. dataframe/text)."""
    if not raw or not isinstance(raw, str):
        return raw or ""
    s = raw.strip()
    if s.startswith("CHART_BASE64:"):
        return s
    # Only treat as chart path if it looks like one (temp_chart + .png); dataframe/text has neither → returned as-is
    path_candidate = s.replace("\\", "/")
    if "temp_chart" not in path_candidate or ".png" not in path_candidate:
        return s
    if "exports" in path_candidate:
        path_candidate = path_candidate[path_candidate.find("exports") :].split()[0]
    path_candidate = path_candidate.strip()
    # Try cwd and package dir (slackbot_agent) where agent often saves charts
    for base in [Path.cwd(), Path(__file__).resolve().parent.parent]:
        chart_path = (base / path_candidate).resolve()
        if chart_path.is_file() and chart_path.suffix.lower() in (".png", ".jpg", ".jpeg"):
            try:
                data = chart_path.read_bytes()
                return "CHART_BASE64:" + base64.b64encode(data).decode()
            except OSError as e:
                logger.debug("Could not read chart file %s: %s", chart_path, e)
    return s


def _table_from_block(block: list[list[str]], intro: str | None) -> str:
    """Build markdown table in a code block from header + data rows."""
    header = "| " + " | ".join(cell.strip() for cell in block[0]) + " |"
    sep_row = "|" + "|".join("---" for _ in block[0]) + "|"
    body = "\n".join("| " + " | ".join(cell.strip() for cell in r) + " |" for r in block[1:])
    table = f"{header}\n{sep_row}\n{body}"
    out = f"```\n{table}\n```"
    if intro:
        out = intro + "\n\n" + out
    return out


def _format_as_table(text: str) -> str | None:
    """If the response looks like a dataframe (header + rows with 2+ spaces), convert to a markdown table."""
    raw_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    lines = [
        ln for ln in raw_lines
        if ln != "..."
        and not re.match(r"\[\d+\s*rows?\s*x\s*\d+\s*columns?\]", ln, re.IGNORECASE)
    ]
    if len(lines) < 2:
        return None

    if "|" in text and lines[0].startswith("|"):
        return f"```\n{text}\n```"

    # Dataframe-style: columns separated by 2+ spaces; optional leading index column
    rows = [re.split(r"\s{2,}", ln) for ln in lines]
    start = next((i for i, r in enumerate(rows) if len(r) >= 2), None)
    if start is None:
        return None
    block = rows[start:]
    if len(block) < 2:
        return None
    ncols = len(block[0])
    if not all(len(r) == ncols for r in block):
        if all(len(r) == ncols + 1 for r in block[1:]) and len(block[0]) == ncols:
            block = [block[0]] + [r[1:] for r in block[1:]]
        else:
            return None
    if not all(len(r) == len(block[0]) for r in block):
        return None
    intro = "\n".join(lines[:start]).strip() if start else ""
    return _table_from_block(block, intro or None)


def build_slack_message(engine_response: str) -> str:
    """
    Build the message to send back to Slack from the engine response.

    - Passes through the response as-is.
    - Truncates at MAX_SLACK_MESSAGE_LENGTH with a trailing note if needed.
    - Normalizes common error phrasing into a short user-facing message.
    """
    if not engine_response or not isinstance(engine_response, str):
        return "I couldn't get a result for that question. Please try rephrasing."

    text = engine_response.strip()

    # If the engine failed (e.g. chart save error), return a friendly message
    if "Code execution failed" in text or "FileNotFoundError" in text:
        return (
            "I ran into an issue generating that result. "
            "For rankings and top-N questions I'll show the data in a table instead. "
            "Try asking again, e.g. \"Show me the top 5 artists by revenue as a table.\""
        )

    # Chart path but file couldn't be read (normalize_chart_response runs first in send_to_slack; this is fallback if file was missing)
    if "temp_chart" in text and ".png" in text and len(text) < 200 and "\n" not in text:
        return "Chart couldn't be displayed. Please try asking for the chart again."

    # Convert to table format when response looks like tabular data (e.g. revenue per artist)
    table_formatted = _format_as_table(text)
    if table_formatted is not None:
        text = table_formatted

    if len(text) <= MAX_SLACK_MESSAGE_LENGTH:
        return text

    return text[: MAX_SLACK_MESSAGE_LENGTH - 20].rstrip() + "\n\n_(message truncated)_"


def send_to_slack(
    engine_response: str,
    *,
    client,
    channel_id: str,
    say,
) -> None:
    """
    Handle the engine response and send to Slack: upload chart image or post formatted text.
    Normalizes chart path to CHART_BASE64 in the response builder so the engine stays simple.

    Parameter
    ----------
    engine_response: str
        The response from the engine.
    client: SlackClient
        The Slack client.
    channel_id: str
        The channel ID.
    say: Callable
        The function to call to send a message to Slack.
    
    """
    if not engine_response or not isinstance(engine_response, str):
        say(build_slack_message(""))
        return

    # Normalize chart path → CHART_BASE64 here (engine returns raw path; we read file and convert)
    engine_response = _normalize_chart_response(engine_response)
    response_stripped = engine_response.strip()
    if response_stripped.startswith("CHART_BASE64:"):
        try:
            raw = base64.b64decode(response_stripped[len("CHART_BASE64:") :])
            client.files_upload_v2(
                channel=channel_id,
                file=io.BytesIO(raw),
                filename="chart.png",
                title="Chart",
            )
        except Exception as e:
            logger.warning("Failed to upload chart: %s", e)
            say(build_slack_message("I couldn't display the chart. Please try again."))
    else:
        say(build_slack_message(engine_response))
