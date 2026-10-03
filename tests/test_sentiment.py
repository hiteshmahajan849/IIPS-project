"""NLP layer unit tests. Covers TC-02 and TC-03 from the SDD test plan
(Chapter 9.8) plus aspect tagging and abusive-comment flagging (FR-09 to
FR-11), and a lightweight accuracy sample check against NFR-08's 80% target.
"""
from app.nlp.analyzer import VaderAnalyzer
from app.nlp.aspects import tag_aspects
from app.nlp.moderation import is_abusive


def test_tc02_negative_hinglish_comment():
    result = VaderAnalyzer().analyze("lectures are bakwas and boring")
    assert result["label"] == "negative"


def test_tc03_positive_hinglish_comment_tags_teaching():
    result = VaderAnalyzer().analyze("teaching was accha and clear")
    assert result["label"] == "positive"
    assert "teaching" in result["aspects"]


def test_neutral_empty_comment():
    result = VaderAnalyzer().analyze("")
    assert result["label"] == "neutral"
    assert result["confidence"] == 0.0


def test_confidence_is_between_0_and_1():
    result = VaderAnalyzer().analyze("This course was absolutely fantastic and well organized.")
    assert 0.0 <= result["confidence"] <= 1.0


def test_aspect_tagging_multiple_aspects():
    aspects = tag_aspects("The projector never works and the teacher explains very fast")
    assert "infrastructure" in aspects
    assert "teaching" in aspects


def test_abusive_comment_flagged():
    assert is_abusive("This teacher is an idiot and useless")


def test_non_abusive_comment_not_flagged():
    assert not is_abusive("The lectures were clear and well explained")


# Hand-labelled sample set exercising the accuracy target in NFR-08
# ("at least 80% agreement with manual labels on a sample set").
LABELLED_SAMPLE = [
    ("Teaching was excellent and very clear.", "positive"),
    ("Mast lectures the, bahut accha laga.", "positive"),
    ("Zabardast course content, well structured.", "positive"),
    ("Labs were helpful and well organized.", "positive"),
    ("Great explanations by the faculty.", "positive"),
    ("Lectures are bakwas and boring.", "negative"),
    ("Ghatiya infrastructure, wifi never works.", "negative"),
    ("This course was a complete waste of time.", "negative"),
    ("Projector is broken and classroom is bad.", "negative"),
    ("Assignments are bekar and confusing.", "negative"),
    ("The course covered the syllabus.", "neutral"),
    ("We had lectures on this topic.", "neutral"),
    ("Exams were held as per schedule.", "neutral"),
]


def test_accuracy_meets_nfr08_target():
    analyzer = VaderAnalyzer()
    correct = sum(1 for text, expected in LABELLED_SAMPLE if analyzer.analyze(text)["label"] == expected)
    accuracy = correct / len(LABELLED_SAMPLE)
    assert accuracy >= 0.8, f"Accuracy {accuracy:.0%} below the 80% target in NFR-08"
