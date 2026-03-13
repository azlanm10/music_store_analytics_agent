import re
import logging
logger = logging.getLogger(__name__)
# Patterns that suggest a column may contain PII.
PII_PATTERNS = [
    r"ssn",
    r"social.?security",
    r"e.?mail",
    r"phone",
    r"credit.?card",
    r"password",
    r"passport",
    r"driver.?licen[sc]e",
    r"date.?of.?birth",
    r"dob",
    r"national.?id",
    r"tax.?id",
]

BLOCKED_PATTERNS = [
    r"delete",
    r"drop",
    r"update",
    r"insert",
    r"alter",
    r"rename",
    r"remove",
    r"truncate",
    r"reset",
    r"ignore.?previous.?instructions",
    r"bypass",
    r"system.?prompt",
    r"you.?are.?an",
    r"you.?are.?now",
    r"act.?as.?a",
    r"modify",
    r"change",
    r"hidden.?prompt"
]

_PII_RE = re.compile("|".join(PII_PATTERNS), re.IGNORECASE)
_BLOCKED_RE = re.compile("|".join(BLOCKED_PATTERNS), re.IGNORECASE)

def check_pii(query: str) -> bool:
    """
    Check if the query contains any PII.
    Returns True if the query contains any PII, False otherwise.
    """
    logger.info("Checking for PII")
    return _PII_RE.search(query) is not None

def check_blocked(query: str) -> bool:
    """
    Check if the query contains any blocked patterns.
    Returns True if the query contains any blocked patterns, False otherwise.
    """
    logger.info("Checking for blocked patterns")
    return _BLOCKED_RE.search(query) is not None
