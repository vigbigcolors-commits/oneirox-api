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


def build_response_limits(budget: ResponseBudget) -> str:
    return (
        f"\n\n---\n"
        f"DREAM LENGTH: {budget.dream_words} words ({budget.tier}).\n"
        f"RESPONSE LIMIT: {budget.word_limit} words total.\n"
        f"[SIGNAL] max {budget.signal_limit} words. "
        f"[BODY] max {budget.body_limit} words (2–3 paragraphs for long dreams). "
        f"[MORNING] max {budget.morning_limit} words.\n"
        f"Match depth to dream complexity. Long dreams need fuller diagnosis — still no padding.\n"
        f"CRITICAL: dreamer = you/your only. Banned: her brain, his brain, Had she. "
        f"Dream characters are built by YOUR brain. "
        f"Open inside the dream or body — not with 'Your brain' or 'Your amygdala'. "
        f"Vary where the clearest answer lands (SIGNAL or middle/end of BODY). No template rhythm."
    )


OTHER_PERSON_DREAM_NOTE = (
    "\n\nCLIENT NOTE: This text describes another person's dreams and/or them leaving the client. "
    "Do NOT attribute REM, amygdala, limbic system, or consolidation to that other person. "
    "Address the typer as YOU — their grief and sense-making only."
)

OTHER_PERSON_DREAM_RE = re.compile(
    r"(?:\b(?:my|her|his)\s+(?:girlfriend|boyfriend|partner|wife|husband|ex)\b.*\b(?:dream|left|broke|dumped|ended)|"
    r"\bshe dreamed\b|\bhe dreamed\b|\bher dreams\b|\bhis dreams\b|"
    r"\bshe left\b.*\bdream|\bdream(?:ed)?\b.*\bshe left\b|\bbroke up\b.*\bdream)",
    re.IGNORECASE,
)

REWRITE_ADDRESS_INSTRUCTION = (
    "REWRITE the full response. You violated ADDRESS / DREAM OWNERSHIP rules.\n"
    "The person who typed the dream is YOU. Their sleep mechanisms are YOUR brain, YOUR amygdala — "
    "never her brain / his brain for the dreamer.\n"
    "If she rejects you IN the dream, YOUR brain built that scene.\n"
    "If the text describes a partner's dreams or breakup: do NOT diagnose her/his REM — decode what it does to YOU.\n"
    "[MORNING] must use Had you / Did you — not Had she / Did he about the dreamer.\n"
    "Keep exact markers [SIGNAL] [BODY] [MORNING]. Same dream. Plain language."
)

REWRITE_ADDRESS_STRICT = (
    "FINAL REWRITE — previous attempt still wrong.\n"
    "Zero instances of: her brain, his brain, her amygdala, her system, her body voted, Had she, Did he.\n"
    "Speak only to the person who typed: YOU / YOUR.\n"
    "If about partner's dreams + breakup: YOU were left. YOU are grieving. What YOUR mind does with her report.\n"
    "Keep [SIGNAL] [BODY] [MORNING]. Plain words. Short sentences."
)


def describes_other_person_dream(dream_text: str) -> bool:
    return bool(OTHER_PERSON_DREAM_RE.search(dream_text))


def build_dream_user_message(dream_text: str, budget: ResponseBudget) -> str:
    msg = f"{build_response_limits(budget)}\n\nDream: {dream_text}"
    if describes_other_person_dream(dream_text):
        msg += OTHER_PERSON_DREAM_NOTE
    return msg


def build_user_message(prompt: str, dream_text: str, budget: ResponseBudget) -> str:
    """Legacy: prompt embedded in user message (local test fallback)."""
    return f"{prompt}{build_dream_user_message(dream_text, budget)}"


def _extract_section(text: str, tag: str) -> str:
    m = re.search(rf"\[{tag}\]([\s\S]*?)(?=\[|$)", text, re.IGNORECASE)
    return m.group(1) if m else ""


def violates_dreamer_address(text: str) -> bool:
    """True when response attributes sleep circuits to her/his brain or wrong MORNING address."""
    if re.search(
        r"\b(?:her|his)\s+(?:brain|amygdala|hippocampus|limbic(?:\s+system)?|"
        r"emotional\s+system|insula|nervous\s+system|system|body)\b",
        text,
        re.IGNORECASE,
    ):
        return True

    if re.search(
        r"\b(?:her|his)\s+(?:consolidation|REM|dream\s+sleep)\b",
        text,
        re.IGNORECASE,
    ):
        return True

    if re.search(r"\b(?:her|his)\s+body\s+voted\b", text, re.IGNORECASE):
        return True

    signal = _extract_section(text, "SIGNAL")
    if signal and re.match(
        r"^\s*(?:Her|His)\b",
        signal,
        re.IGNORECASE,
    ):
        return True

    morning = _extract_section(text, "MORNING")
    if morning and re.search(r"\bHad\s+(?:she|he)\b", morning, re.IGNORECASE):
        return True

    return False
