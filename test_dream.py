"""Local dream test — same prompt, validation, and model as main.py."""

import re
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv
import os

from dream_validation import build_user_message, classify_input, get_response_budget, sanitize_decode_output, validate_dream

load_dotenv()

ROOT = Path(__file__).resolve().parent
PROMPT = (ROOT / "ONEIROX_PROMPT.txt").read_text(encoding="utf-8").strip()
MODEL = "claude-sonnet-4-5"


def parse_section(text: str, tag: str) -> str:
    m = re.search(rf"\[{tag}\]([\s\S]*?)(?=\[|$)", text)
    return m.group(1).strip() if m else ""


def analyze(dream_text: str) -> tuple[str, object]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY not set. Add it to .env in this folder.")

    validate_dream(dream_text)
    mode = classify_input(dream_text)
    lang = "ru" if re.search(r"[а-яА-ЯёЁ]", dream_text) else "en"
    budget = get_response_budget(dream_text, mode)
    print(f"Dream: {budget.dream_words} words -> mode: {mode}, lang: {lang}, tier: {budget.tier}, limit: {budget.word_limit} words\n")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=MODEL,
        max_tokens=budget.max_tokens,
        messages=[
            {
                "role": "user",
                "content": build_user_message(PROMPT, dream_text, budget, mode, lang=lang),
            }
        ],
    )
    raw = sanitize_decode_output(message.content[0].text)
    return raw, budget


def read_dream() -> str:
    args = sys.argv[1:]

    if not args:
        print("Paste your dream. When done: empty line + Enter.\n")
        lines = []
        while True:
            line = input()
            if line == "" and lines:
                break
            lines.append(line)
        return "\n".join(lines).strip()

    if args[0] in ("-f", "--file"):
        if len(args) < 2:
            sys.exit("Usage: py test_dream.py --file dream.txt")
        path = Path(args[1])
        if not path.is_file():
            sys.exit(f"File not found: {path}")
        return path.read_text(encoding="utf-8").strip()

    if len(args) == 1 and Path(args[0]).is_file():
        return Path(args[0]).read_text(encoding="utf-8").strip()

    if len(args) == 1 and len(args[0]) > 200:
        print("Tip: for long dreams, save to dream.txt and run: py test_dream.py dream.txt")

    return " ".join(args).strip()


def main() -> None:
    dream = read_dream()
    if not dream:
        sys.exit("No dream text provided.")

    try:
        print("\nReading…\n")
        raw, budget = analyze(dream)
    except ValueError as e:
        sys.exit(f"Rejected (no API call): {e}")

    word_count = len(raw.split())
    over = word_count > budget.word_limit

    print("=" * 60)
    print(f"RAW ({word_count} words, limit {budget.word_limit}{' — OVER' if over else ''})")
    print("=" * 60)
    print(raw)

    signal = parse_section(raw, "SIGNAL")
    body = parse_section(raw, "BODY")
    morning = parse_section(raw, "MORNING")

    if signal or body or morning:
        print("\n" + "=" * 60)
        print("PARSED (as on oneirox.com)")
        print("=" * 60)
        if signal:
            print(f"\n[SIGNAL]\n{signal}")
        if body:
            print(f"\n[BODY]\n{body}")
        if morning:
            print(f"\n[MORNING]\n{morning}")


if __name__ == "__main__":
    main()
