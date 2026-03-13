import logging

logger = logging.getLogger(__name__)

MUSIC_KEYWORDS = [
    "music",
    "song",
    "track",
    "artist",
    "album",
    "genre",
    "playlist",
    "customer",
    "invoice",
    "sales",
    "revenue",
    "country",
]


def has_music_keywords(text: str) -> bool:
    """Return True if the text contains any music-store keyword (case-insensitive)."""
    if not text:
        return False
    return any(keyword in text.lower() for keyword in MUSIC_KEYWORDS)


def validate_query(query: str) -> dict[str, bool | str]:
    """
    Validate the query to ensure it is related to the music store domain.
    The check is case-insensitive.

    Returns a dict with:
    - "passed" (bool): True if the query is in-domain, False otherwise.
    - "query" (str): Lowercased query when passed is True.
    - "message" (str): Error message when passed is False.
    """

    logger.info("Running validator")

    query = query.lower()

    if any(keyword in query for keyword in MUSIC_KEYWORDS):
        logger.info("Validator passed")
        return {
            "passed": True,
            "query": query
        }

    logger.warning("Validator failed: query outside music store domain")
    return {
        "passed": False,
        "message": "Sorry, I can only answer questions related to the music store database."
    }