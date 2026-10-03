"""Hinglish sentiment lexicon additions for VADER (FR-08).

VADER's bundled lexicon is English-only. Common Hinglish (Romanized Hindi)
words used in Indian student feedback are added here with VADER-style
valence scores (-4 to +4) so the same VADER engine can score mixed
English/Hinglish comments without a paid translation API.
"""

HINGLISH_LEXICON: dict[str, float] = {
    # Positive
    "accha": 1.8, "achha": 1.8, "acha": 1.8,
    "badiya": 2.2, "badia": 2.2,
    "mast": 2.0, "zabardast": 2.5, "jabardast": 2.5,
    "bahut": 0.3, "bohot": 0.3,  # intensifier-ish, mild positive on its own
    "shandar": 2.6, "umda": 2.0,
    "sahi": 1.6, "theek": 1.0, "thik": 1.0,
    "kamaal": 2.3, "faydemand": 1.8, "madadgar": 1.7,
    "pasand": 1.5,
    # Negative
    "bakwas": -2.5, "bekar": -2.0, "bekaar": -2.0,
    "ghatiya": -2.5, "faltu": -2.0,
    "bore": -1.6, "boring": -1.8,
    "bura": -1.8, "kharab": -2.0,
    "mushkil": -1.0, "pareshani": -1.8, "dikkat": -1.5,
    "bakar": -2.2, "waste": -1.8,
    "slow": -0.8, "confuse": -1.2, "confusing": -1.4,
}
