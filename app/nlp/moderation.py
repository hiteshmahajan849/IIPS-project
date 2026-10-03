"""Abusive / inappropriate comment detection (FR-11).

A conservative open-source keyword-and-pattern approach: no paid moderation
API is used. This deliberately flags for *human* review rather than silently
deleting content — final approve/remove is an Admin action (state machine in
Chapter 4.7: Analyzed -> Flagged -> Published/Rejected).
"""
import re

# Profanity and direct personal-insult markers (English and Romanized
# Hindi/Hinglish), kept deliberately narrow so merely *negative* feedback
# ("bakwas", "useless", "pathetic" describing a course or facility) is left
# to the sentiment analyzer and is NOT routed to moderation -- only content
# that is abusive/inappropriate (profanity, slurs, insults aimed at a
# person) should be flagged for Admin review (FR-11). Extend this list as
# needed; it is a plain data file so no code changes are required to tune it.
ABUSIVE_TERMS = {
    "idiot", "stupid", "shut up", "hate you", "fool", "moron", "dumb",
    "shit", "damn", "bloody", "bastard", "jerk",
    "chutiya", "harami", "haraami", "kamina", "kaminey", "saala", "saale",
    "madarchod", "behenchod", "bhenchod", "gandu", "randi", "chutiye",
    "nalayak", "nikamma",
}

_WORD_RE = re.compile(r"[a-zA-Z]+")


def is_abusive(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    tokens = set(_WORD_RE.findall(lowered))
    if tokens & ABUSIVE_TERMS:
        return True
    # multi-word phrases
    return any(phrase in lowered for phrase in ABUSIVE_TERMS if " " in phrase)
