"""Help / capability detection and response for the music store bot."""

import re
from pathlib import Path

_HELP_RESPONSE_PATH = Path(__file__).resolve().parent / "help_response.txt"

HELP_PATTERNS = [

    # direct help
    r"\bhelp\b",
    r"\bhelp\s+me\b",

    # what can you do (and e.g. "what can you do for me")
    r"what\s+can\s+you\s+do",
    r"what\s+can\s+you\s+help\s+with",
    r"how\s+can\s+you\s+help",
    r"what\s+do\s+you\s+do",

    # capabilities
    r"what\s+are\s+your\s+capabilities",
    r"capabilities",
    r"what\s+are\s+you\s+able\s+to\s+do",

    # dataset questions
    r"tell\s+me\s+about\s+the\s+dataset",
    r"tell\s+me\s+about\s+the\s+data",
    r"what\s+data\s+do\s+you\s+have",
    r"what\s+data\s+is\s+available",

    # database questions
    r"what'?s\s+in\s+the\s+database",
    r"what\s+is\s+in\s+the\s+database",
    r"what\s+tables\s+are\s+there",
    r"what\s+tables\s+exist",
    r"show\s+the\s+tables",

    # usage questions
    r"how\s+do\s+i\s+use\s+you",
    r"how\s+does\s+this\s+work",
    r"how\s+can\s+i\s+use\s+this",
    r"what\s+can\s+i\s+ask",

    # general bot identity
    r"who\s+are\s+you",
    r"what\s+are\s+you",
    r"what\s+is\s+this\s+bot",
    r"what\s+can\s+you\s+do"
]
_HELP_RE = re.compile(
    "|".join(re.escape(p) for p in HELP_PATTERNS),
    re.IGNORECASE,
)


def _load_help_response() -> str:
    """Load help response text from help_response.txt."""
    return _HELP_RESPONSE_PATH.read_text(encoding="utf-8").strip()


def get_help_response() -> str:
    """Return the help/dataset description (loaded from file)."""
    return _load_help_response()


# Exposed for backward compatibility; loaded from help_response.txt
HELP_RESPONSE = _load_help_response()


def is_help_request(text: str) -> bool:
    """True if the message is asking what the bot can do (no validation needed)."""
    return _HELP_RE.search((text or "").strip()) is not None


# Greetings: short messages like "hey", "hi", "hello" get a friendly reply instead of out-of-domain
GREETING_PATTERNS = [
    r"^hey!?\s*$",
    r"^heya!?\s*$",
    r"^hi!?\s*$",
    r"^hello!?\s*$",
    r"^hey\s+there\s*$",
    r"^hi\s+there\s*$",
    r"^hello\s+there\s*$",
    r"^howdy\s*$",
    r"^yo\s*$",
]
_GREETING_RE = re.compile("|".join(GREETING_PATTERNS), re.IGNORECASE)

GREETING_RESPONSE = "Hello, how can I help you today?"


def is_greeting(text: str) -> bool:
    """True if the message is just a greeting (hey, hi, hello, etc.)."""
    return _GREETING_RE.search((text or "").strip()) is not None
