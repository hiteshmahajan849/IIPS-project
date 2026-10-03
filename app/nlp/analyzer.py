"""NLP Layer: sentiment analysis (FR-08, FR-09). Design patterns in play:

- Strategy: `SentimentAnalyzer` is the interface; `VaderAnalyzer` is one
  concrete strategy. A future `TransformerAnalyzer` can be dropped in
  without changing `FeedbackService` (NFR-07).
- Factory: `get_analyzer(name)` builds the configured strategy from config.
- Singleton: each concrete analyzer is cached so the VADER lexicon (plus the
  Hinglish additions) is loaded once per process, not once per request.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from functools import lru_cache

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .aspects import tag_aspects
from .hinglish_lexicon import HINGLISH_LEXICON
from .moderation import is_abusive

_URL_RE = re.compile(r"https?://\S+")
_WHITESPACE_RE = re.compile(r"\s+")

POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


class SentimentAnalyzer(ABC):
    """Strategy interface. Any implementation must return a dict with keys:
    label ('positive'|'neutral'|'negative'), score (float, -1..1),
    confidence (float, 0..1), aspects (list[str]), is_abusive (bool)."""

    @abstractmethod
    def analyze(self, text: str) -> dict:
        raise NotImplementedError

    @staticmethod
    def clean(text: str) -> str:
        """Preprocessing shared by all strategies (FR-08): strip URLs,
        collapse whitespace. Lowercasing is left to the strategy since VADER
        itself is case-sensitive (ALL CAPS boosts intensity)."""
        text = _URL_RE.sub(" ", text or "")
        return _WHITESPACE_RE.sub(" ", text).strip()


class VaderAnalyzer(SentimentAnalyzer):
    """VADER (lexicon + rule based) extended with a Hinglish lexicon so
    mixed English/Hindi-Romanized comments score sensibly without any paid
    translation or classification API (Chapter 9.5 sentiment design)."""

    def __init__(self):
        self._vader = SentimentIntensityAnalyzer()
        self._vader.lexicon.update(HINGLISH_LEXICON)

    def analyze(self, text: str) -> dict:
        cleaned = self.clean(text)
        if not cleaned:
            return {"label": "neutral", "score": 0.0, "confidence": 0.0,
                     "aspects": [], "is_abusive": False}

        compound = self._vader.polarity_scores(cleaned)["compound"]
        if compound >= POSITIVE_THRESHOLD:
            label = "positive"
        elif compound <= NEGATIVE_THRESHOLD:
            label = "negative"
        else:
            label = "neutral"

        return {
            "label": label,
            "score": round(compound, 4),
            "confidence": round(abs(compound), 4),
            "aspects": tag_aspects(cleaned),
            "is_abusive": is_abusive(cleaned),
        }


@lru_cache(maxsize=None)
def _build_analyzer(name: str) -> SentimentAnalyzer:
    registry = {"vader": VaderAnalyzer}
    if name not in registry:
        raise ValueError(f"Unknown sentiment analyzer: {name}")
    return registry[name]()


def get_analyzer(name: str = "vader") -> SentimentAnalyzer:
    """Factory + Singleton: returns the cached analyzer instance for `name`."""
    return _build_analyzer(name)
