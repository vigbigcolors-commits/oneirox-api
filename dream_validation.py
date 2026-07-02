"""Dream input validation and dynamic response budgets."""

import re
from dataclasses import dataclass

MIN_WORDS = 8
MIN_CHARS = 40
MAX_CHARS = 8000

VOWELS = re.compile(r"[aeiouyаеёиоуыэюя]", re.IGNORECASE)
WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


@dataclass(frozen=True)
class ResponseBudget:
    dream_words: int
    word_limit: int
    body_limit: int
    morning_limit: int
    signal_limit: int
    max_tokens: int
    tier: str


def dream_word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def validate_dream(text: str) -> None:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Describe your dream in a few sentences.")

    if len(cleaned) < MIN_CHARS:
        raise ValueError("Dream is too short. Add more detail about what happened.")

    if len(cleaned) > MAX_CHARS:
        raise ValueError("Dream is too long. Please shorten to under 8000 characters.")

    words = [w.lower() for w in WORD_RE.findall(cleaned)]
    if len(words) < MIN_WORDS:
        raise ValueError("Not enough detail. Describe the dream scene, feeling, and what woke you.")

    if len(set(words)) <= 2 and len(words) >= 6:
        raise ValueError("This doesn't read like a dream description.")

    if " " not in cleaned and len(cleaned) > 25:
        raise ValueError("This doesn't read like a dream description.")

    letters = sum(1 for c in cleaned if c.isalpha())
    if letters / len(cleaned) < 0.55:
        raise ValueError("This doesn't read like a dream description.")

    long_words = [w for w in words if len(w) >= 4]
    if long_words:
        with_vowels = sum(1 for w in long_words if VOWELS.search(w))
        if with_vowels / len(long_words) < 0.35:
            raise ValueError("This doesn't read like a dream description.")

    if max(len(w) for w in words) > 22:
        raise ValueError("This doesn't read like a dream description.")

    if re.search(r"(.)\1{6,}", cleaned):
        raise ValueError("This doesn't read like a dream description.")

    if re.search(r"(.{2,5})\1{5,}", cleaned.lower()):
        raise ValueError("This doesn't read like a dream description.")


def get_response_budget(text: str) -> ResponseBudget:
    words = dream_word_count(text)

    if words < 40:
        return ResponseBudget(
            dream_words=words,
            word_limit=220,
            body_limit=150,
            morning_limit=20,
            signal_limit=25,
            max_tokens=350,
            tier="short",
        )
    if words < 120:
        return ResponseBudget(
            dream_words=words,
            word_limit=300,
            body_limit=220,
            morning_limit=25,
            signal_limit=30,
            max_tokens=500,
            tier="standard",
        )
    if words < 300:
        return ResponseBudget(
            dream_words=words,
            word_limit=400,
            body_limit=310,
            morning_limit=30,
            signal_limit=35,
            max_tokens=650,
            tier="long",
        )
    return ResponseBudget(
        dream_words=words,
        word_limit=500,
        body_limit=400,
        morning_limit=35,
        signal_limit=40,
        max_tokens=800,
        tier="detailed",
    )


def build_user_message(prompt: str, dream_text: str, budget: ResponseBudget) -> str:
    limits = (
        f"\n\n---\n"
        f"DREAM LENGTH: {budget.dream_words} words ({budget.tier}).\n"
        f"RESPONSE LIMIT: {budget.word_limit} words total.\n"
        f"[SIGNAL] max {budget.signal_limit} words. "
        f"[BODY] max {budget.body_limit} words (2–3 paragraphs for long dreams). "
        f"[MORNING] max {budget.morning_limit} words.\n"
        f"Match depth to dream complexity. Long dreams need fuller diagnosis — still no padding.\n"
        f"Every brain term: name (plain words in parentheses). Typer = you/your."
    )
    note = ""
    if re.search(
        r"\b(?:she|her)\s+(?:dream|dreamed|dreamt|left|broke up)|"
        r"\b(?:my|her)\s+(?:girlfriend|boyfriend|partner|ex|wife|husband)\b",
        dream_text,
        re.IGNORECASE,
    ):
        note = (
            "\n\nCLIENT: Partner/ex dream or breakup story. Address typer as YOU. "
            "Banned in output: her brain, her amygdala, her limbic, Had she."
        )
    return f"{prompt}{limits}{note}\n\nDream: {dream_text}"
