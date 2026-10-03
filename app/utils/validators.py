"""Small, dependency-free input validation helpers used by controllers."""
from __future__ import annotations

ASPECT_NAMES = ("teaching", "content", "labs", "infrastructure", "assessment")


class ValidationError(Exception):
    pass


def parse_ratings(form) -> dict[str, int]:
    """Validates and extracts the five 1-5 aspect ratings from a form.
    Raises ValidationError with a human-readable message on bad input."""
    scores: dict[str, int] = {}
    for aspect in ASPECT_NAMES:
        raw = form.get(aspect)
        if raw is None or raw == "":
            raise ValidationError(f"Please rate '{aspect}'.")
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValidationError(f"Rating for '{aspect}' must be a number.") from exc
        if not (1 <= value <= 5):
            raise ValidationError(f"Rating for '{aspect}' must be between 1 and 5.")
        scores[aspect] = value
    return scores


def clean_comment(raw: str | None, max_len: int = 2000) -> str:
    comment = (raw or "").strip()
    if len(comment) > max_len:
        raise ValidationError(f"Comment must be under {max_len} characters.")
    return comment


def is_valid_email(email: str) -> bool:
    email = (email or "").strip()
    return "@" in email and "." in email.split("@")[-1] and len(email) <= 254
