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
            word_limit=320,
            body_limit=240,
            morning_limit=28,
            signal_limit=32,
            max_tokens=550,
            tier="standard",
        )
    if words < 300:
        return ResponseBudget(
            dream_words=words,
            word_limit=420,
            body_limit=330,
            morning_limit=32,
            signal_limit=38,
            max_tokens=700,
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
    notes: list[str] = []
    if re.search(
        r"\b(?:she|her)\s+(?:dream|dreamed|dreamt|left|broke up)|"
        r"\b(?:my|her)\s+(?:girlfriend|boyfriend|partner|ex|wife|husband)\b",
        dream_text,
        re.IGNORECASE,
    ):
        notes.append(
            "\n\nCLIENT: Partner/ex dream or breakup. Typer = YOU only for neuroscience. "
            "BANNED even with parentheses: her brain, her amygdala, her limbic, her system, her REM, Had she. "
            "Use: she told you / she left + your grief, your shock, your mind scanning. "
            "Every science term: name (plain words in parentheses)."
        )
    if re.search(
        r"\b(?:recurring|same dream|exact same dream|never changed|"
        r"for (?:almost )?(?:\d+\s*)?(?:years|yrs|decades|two decades)|"
        r"since (?:I was|childhood|age \d)|sleep paralysis|sleep\s+paralysis|"
        r"\bparalysis\b|atonia|lucid(?:ity)?|partial wake|watcher on a hill)\b",
        dream_text,
        re.IGNORECASE,
    ):
        notes.append(
            "\n\nCLIENT: Recurring dream and/or sleep paralysis. Physiology first — NOT therapy. "
            "Stack: REM atonia (muscle lock during dream sleep) + sympathetic arousal (fire, fight) + "
            "Revonsuo threat simulation (same drill, not prophecy). "
            "Watcher on hill = immobilized observer projected outward — NOT a childhood person to identify. "
            "Lucidity: somatic trigger mapping (breath, chest, temperature, heart rate before meadow) — "
            "NOT interrogating dream characters. "
            "MORNING: one somatic/body question only. BANNED: Who in your early life, Who watched you, "
            "suppressed memory, attachment figure."
        )
    note = "".join(notes)
    return f"{prompt}{limits}{note}\n\nDream: {dream_text}"


_ORGAN = (
    r"amygdala|hippocampus|limbic(?:\s+system)?|insula|thalamus|"
    r"prefrontal cortex|nervous system|emotional(?:\s+system)?"
)


def sanitize_decode_output(text: str) -> str:
    """
    Last-line guard: never ship another person's brain/organ diagnosis.
    Zero extra API calls — runs on every response before return.
    """
    out = text

    phrase_fixes = [
        (rf"\bHer\s+(?:{_ORGAN})\s*\([^)]*\)\s+was\s+staging", "In what she told you, the dream was staging"),
        (rf"\bHer\s+(?:{_ORGAN})\s*\([^)]*\)\s+rehearsed", "In what she described, rejection replayed"),
        (rf"\bher\s+(?:{_ORGAN})\s*\([^)]*\)\s+was\s+", "what she reported was "),
        (r"\b[Tt]hat's\s+her brain\s+running\s+a\s+drill", "She kept having the same dream"),
        (r"\bher brain was already working\b", "she was already wrestling with something"),
        (r"\bHer brain was already working\b", "She was already wrestling with something"),
        (r"\bher brain was already\b", "she was already"),
        (r"\bHer brain was already\b", "She was already"),
        (r"\bher brain ran\b", "she reported dreams where"),
        (r"\bHer brain ran\b", "She reported dreams where"),
        (r"\bher limbic system\s+is\s+running\b", "you are processing"),
        (r"\bHer limbic system\s+is\s+running\b", "You are processing"),
        (r"\bsuppressed memory waiting to confess\b", "a cognitive placeholder for motor lock during atonia"),
        (
            r"\bThe watcher on the hill isn't waiting for questions\b",
            "The watcher is not a person to interrogate—it is your immobilized state projected outward",
        ),
        (
            r"\bsomeone who sees you struggle and chooses distance\b",
            "your paralyzed observer position projected outward during atonia",
        ),
        (
            r"\bThe watcher represents the thing you have not been able to change\b",
            "The watcher maps the stillness of atonia while your body runs a threat drill",
        ),
    ]
    for pattern, repl in phrase_fixes:
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)

    out = re.sub(
        rf"\bHer\s+(?:{_ORGAN})\s*\([^)]*\)",
        "What she told you from her dreams",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        rf"\bher\s+(?:{_ORGAN})\s*\([^)]*\)",
        "what she told you from her dreams",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        rf"\bHer\s+(?:{_ORGAN})\b",
        "What she reported",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        rf"\bher\s+(?:{_ORGAN})\b",
        "what she reported",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(r"\bHer brain\s*\([^)]*\)", "What she told you", out, flags=re.IGNORECASE)
    out = re.sub(r"\bher brain\s*\([^)]*\)", "what she told you", out, flags=re.IGNORECASE)
    out = re.sub(r"\bHer brain\b", "She", out)
    out = re.sub(r"\bher brain\b", "she", out, flags=re.IGNORECASE)
    out = re.sub(r"\bHis brain\b", "He", out)
    out = re.sub(r"\bhis brain\b", "he", out, flags=re.IGNORECASE)
    out = re.sub(r"\bher fear alarm\b", "what she feared", out, flags=re.IGNORECASE)
    out = re.sub(r"\bher system\b", "what she described", out, flags=re.IGNORECASE)
    out = re.sub(r"\bher REM\b", "her dreams", out, flags=re.IGNORECASE)

    morning = re.search(r"(\[MORNING\])([\s\S]*)", out, re.IGNORECASE)
    if morning:
        tail = morning.group(2)
        tail = _fix_morning_question(tail)
        out = out[: morning.start(2)] + tail

    out = re.sub(r"([.!?]\s+)she ", r"\1She ", out)
    out = re.sub(r"  +", " ", out)
    return out.strip()


def _fix_morning_question(tail: str) -> str:
    """Fix MORNING without breaking 'Did she tell you' partner questions."""
    # Repair bad output from older blanket Had she → Had you
    tail = re.sub(r"\bHad you told you\b", "Did she tell you", tail, flags=re.IGNORECASE)
    tail = re.sub(r"\bDid you told you\b", "Did she tell you", tail, flags=re.IGNORECASE)

    partner_ok = [
        (r"\bHad she told you\b", "Did she tell you"),
        (r"\bHad she mentioned\b", "Did she mention"),
        (r"\bHad she said\b", "Did she say"),
        (r"\bHad she ever told you\b", "Did she ever tell you"),
    ]
    for pattern, repl in partner_ok:
        tail = re.sub(pattern, repl, tail, flags=re.IGNORECASE)

    # Questions wrongly about her inner state → back to the dreamer
    tail = re.sub(r"\bHad she named\b", "Had you already named", tail, flags=re.IGNORECASE)
    tail = re.sub(r"\bHad she been pulling back\b", "Had you noticed her pulling back", tail, flags=re.IGNORECASE)
    tail = re.sub(r"\bHad she said yes out loud\b", "Had you said yes out loud", tail, flags=re.IGNORECASE)

    # Therapy / childhood fishing → somatic redirect (Oneirox positioning)
    somatic_q = (
        "What does your chest or breathing do in the seconds before "
        "the meadow goes dark and your body locks?"
    )
    therapy_patterns = [
        r"Who in your early life[^?]*\?",
        r"Who[^?]{0,80}watched you[^?]*\?",
        r"Who[^?]{0,80}stayed on the hill[^?]*\?",
        r"Who[^?]{0,80}(?:childhood|growing up)[^?]*\?",
        r"What[^?]{0,60}(?:mother|father|parent)[^?]*\?",
    ]
    for pattern in therapy_patterns:
        if re.search(pattern, tail, flags=re.IGNORECASE):
            tail = re.sub(pattern, somatic_q, tail, flags=re.IGNORECASE, count=1)
            break

    return tail
