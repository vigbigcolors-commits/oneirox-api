"""Dream input validation and dynamic response budgets."""

import re
from dataclasses import dataclass

MIN_WORDS = 8
MIN_CHARS = 40
MAX_CHARS = 8000

# Sleep-science questions (not dream reports) — lighter bar
QUESTION_MIN_CHARS = 15
QUESTION_MIN_WORDS = 4

VOWELS = re.compile(r"[aeiouyаеёиоуыэюя]", re.IGNORECASE)
WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)

_SLEEP_Q_START = re.compile(
    r"^(?:how|what|why|when|can|does|do|is|are|will|should)\b",
    re.IGNORECASE,
)
_SLEEP_TOPIC = re.compile(
    r"\b(?:sleep|dream(?:ing)?|rem|insomnia|nap|circadian|melatonin|temperature|"
    r"thermostat|air conditioning|air-conditioning|\bac\b|pillow|mattress|snor|"
    r"apnea|paralysis|nightmare|wake|waking|nrem|deep sleep|light sleep|bedroom|"
    r"cool(?:ing|er)?|heat|humidity)\b",
    re.IGNORECASE,
)
_DREAM_NARRATIVE = re.compile(
    r"\b(?:i dream(?:ed|t|ing)?|in my dream|last night|woke up|woke from|"
    r"i was (?:running|flying|falling|trapped|chasing|in)|i couldn't move|"
    r"i saw|i felt|nightmare|keep dreaming|dreaming about|my dream)\b",
    re.IGNORECASE,
)


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


def _strip_somatic_context(text: str) -> str:
    return re.split(r"\n\n\[SOMATIC CONTEXT", text, maxsplit=1)[0].strip()


def classify_input(text: str) -> str:
    """Return 'dream' or 'sleep_question'."""
    main = _strip_somatic_context(text)

    if _DREAM_NARRATIVE.search(main):
        return "dream"

    if _SLEEP_Q_START.match(main) and _SLEEP_TOPIC.search(main):
        return "sleep_question"

    if main.rstrip().endswith("?") and _SLEEP_TOPIC.search(main):
        return "sleep_question"

    return "dream"


def validate_dream(text: str) -> str:
    """Validate input. Returns 'dream' or 'sleep_question'. Raises ValueError if rejected."""
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Describe your dream in a few sentences.")

    if len(cleaned) > MAX_CHARS:
        raise ValueError("Dream is too long. Please shorten to under 8000 characters.")

    mode = classify_input(cleaned)
    main = _strip_somatic_context(cleaned)
    words = [w.lower() for w in WORD_RE.findall(main)]

    if mode == "sleep_question":
        if len(main) < QUESTION_MIN_CHARS:
            raise ValueError(
                "Question too short. Ask a full sleep-science question "
                "(e.g. how does room temperature affect deep sleep?)."
            )
        if len(words) < QUESTION_MIN_WORDS:
            raise ValueError(
                "Question too short. Ask a full sleep-science question "
                "(e.g. how does room temperature affect deep sleep?)."
            )
        return mode

    if len(cleaned) < MIN_CHARS:
        raise ValueError(
            "Your dream is too brief for a neural reading. "
            "Describe what you saw, what you felt in your body, and what woke you — "
            "even a few sentences."
        )

    if len(words) < MIN_WORDS:
        raise ValueError(
            "Not enough detail for a dream reading. "
            "Add the scene, a body feeling, and what happened when you woke."
        )

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

    return mode


def get_response_budget(text: str, mode: str = "dream") -> ResponseBudget:
    if mode == "sleep_question":
        words = dream_word_count(_strip_somatic_context(text))
        return ResponseBudget(
            dream_words=words,
            word_limit=200,
            body_limit=130,
            morning_limit=22,
            signal_limit=28,
            max_tokens=350,
            tier="short",
        )

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


def build_user_message(prompt: str, dream_text: str, budget: ResponseBudget, mode: str = "dream") -> str:
    limits = (
        f"\n\n---\n"
        f"INPUT MODE: {mode}.\n"
        f"DREAM LENGTH: {budget.dream_words} words ({budget.tier}).\n"
        f"RESPONSE LIMIT: {budget.word_limit} words total.\n"
        f"[SIGNAL] max {budget.signal_limit} words. "
        f"[BODY] max {budget.body_limit} words (2–3 paragraphs for long dreams). "
        f"[MORNING] max {budget.morning_limit} words.\n"
        f"Match depth to dream complexity. Long dreams need fuller diagnosis — still no padding.\n"
        f"Every brain term: name (plain words in parentheses). Typer = you/your.\n"
        f"PRECISION CALMS: clinical term first, bridge second — ban biological gate, metabolic alertness, brain clears waste.\n"
        f"OPENING CANON: never start [SIGNAL] or BODY para 1 with Your brain/amygdala/thalamus/hippocampus."
    )
    if budget.tier != "short":
        limits += "\nQUICK ANSWER: required mid-BODY — plain 1-2 sentences after para 1."
    notes: list[str] = []
    if mode == "sleep_question":
        notes.append(
            "\n\nCLIENT: Sleep-science question — NOT a dream report. "
            "PRECISION CALMS: minimum 3 named mechanisms (hypothalamic thermoregulation, vasodilation, "
            "cortical micro-arousals, etc.) — each with (plain words). "
            "BANNED: biological gate, metabolic alertness, brain clears waste. "
            "Quick answer plain; BODY carries precision stack. Same SIGNAL/BODY/MORNING format."
        )
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
    label = "Question" if mode == "sleep_question" else "Dream"
    return f"{prompt}{limits}{note}\n\n{label}: {dream_text}"


_ORGAN = (
    r"amygdala|hippocampus|limbic(?:\s+system)?|insula|thalamus|"
    r"prefrontal cortex|nervous system|emotional(?:\s+system)?"
)

_BANNED_OPENER = re.compile(
    r"^Your\s+(?:brain|amygdala|hippocampus|thalamus|limbic(?:\s+system)?|"
    r"insula|brainstem|prefrontal\s+cortex)\b",
    re.IGNORECASE,
)

_OPENER_REWRITES = [
    (r"^Your brain is not (.+)$", r"You are not \1"),
    (r"^Your brain isn't (.+)$", r"You aren't \1"),
    (r"^Your brain is (.+)$", r"This is \1"),
    (r"^Your brain has (.+)$", r"You have \1"),
    (r"^Your brain was (.+)$", r"This was \1"),
    (r"^Your brain does not (.+)$", r"This does not \1"),
    (r"^Your brain doesn't (.+)$", r"This doesn't \1"),
    (r"^Your brain ran (.+)$", r"Your body ran \1"),
    (r"^Your brain (.+)$", r"You \1"),
    (r"^Your amygdala (.+)$", r"The fear circuit \1"),
    (r"^Your thalamus (.+)$", r"The relay gate \1"),
    (r"^Your hippocampus (.+)$", r"The memory map \1"),
    (r"^Your limbic system (.+)$", r"The emotional loop \1"),
    (r"^Your prefrontal cortex (.+)$", r"Your logic center \1"),
    (r"^Your insula (.+)$", r"The body-sense layer \1"),
    (r"^Your brainstem (.+)$", r"The autonomic core \1"),
]


def _rewrite_banned_opener(sentence: str) -> str:
    s = sentence.strip()
    if not _BANNED_OPENER.match(s):
        return s
    for pattern, repl in _OPENER_REWRITES:
        if re.match(pattern, s, re.IGNORECASE):
            return re.sub(pattern, repl, s, count=1, flags=re.IGNORECASE)
    return re.sub(r"^Your brain\s+", "You ", s, count=1, flags=re.IGNORECASE)


def _fix_first_sentence(block: str) -> str:
    block = block.strip()
    if not block:
        return block
    m = re.match(r"^([^.!?]+[.!?])(\s*)([\s\S]*)", block)
    if not m:
        return _rewrite_banned_opener(block)
    first, sep, rest = m.group(1), m.group(2), m.group(3)
    fixed_first = _rewrite_banned_opener(first)
    return fixed_first + sep + rest


def _fix_banned_openings(text: str) -> str:
    signal_m = re.search(r"(\[SIGNAL\]\s*)([\s\S]*?)(?=\[BODY\]|$)", text, re.IGNORECASE)
    if signal_m:
        raw_content = signal_m.group(2)
        stripped = raw_content.strip()
        if stripped:
            fixed = _fix_first_sentence(stripped)
            if fixed != stripped:
                lead = re.match(r"^\s*", raw_content).group(0)
                trail = re.search(r"\s*$", raw_content).group(0)
                text = text[: signal_m.start(2)] + lead + fixed + trail + text[signal_m.end(2) :]

    body_m = re.search(r"(\[BODY\]\s*)([\s\S]*?)(?=\[MORNING\]|$)", text, re.IGNORECASE)
    if body_m:
        raw_content = body_m.group(2)
        stripped = raw_content.strip()
        if stripped:
            paras = re.split(r"\n\s*\n", stripped)
            fixed_p0 = _fix_first_sentence(paras[0])
            if fixed_p0 != paras[0]:
                paras[0] = fixed_p0
                lead = re.match(r"^\s*", raw_content).group(0)
                trail = re.search(r"\s*$", raw_content).group(0)
                text = (
                    text[: body_m.start(2)]
                    + lead
                    + "\n\n".join(paras)
                    + trail
                    + text[body_m.end(2) :]
                )
    return text


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
        (r"\bsuppressed memory waiting to confess\b", "cognitive placeholder for motor lock during atonia"),
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

    out = _fix_banned_openings(out)

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
    out = re.sub(r"\ba a\b", "a", out, flags=re.IGNORECASE)
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
