from fastapi import FastAPI, Request, HTTPException
from collections import defaultdict
from pathlib import Path
import hashlib
import time
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import os
from dotenv import load_dotenv

from dream_validation import (
    REWRITE_ADDRESS_INSTRUCTION,
    REWRITE_ADDRESS_STRICT,
    build_dream_user_message,
    get_response_budget,
    validate_dream,
    violates_dreamer_address,
)

load_dotenv()

app = FastAPI(title="Oneirox API")
# Rate limiting: 5 запросов в час с одного IP
request_counts = defaultdict(list)
RATE_LIMIT = 5
RATE_WINDOW = 3600

MODEL = "claude-sonnet-4-5"
PROMPT_PATH = Path(__file__).resolve().parent / "ONEIROX_PROMPT.txt"


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def prompt_sha12() -> str:
    return hashlib.sha256(load_prompt().encode("utf-8")).hexdigest()[:12]


def check_rate_limit(ip: str):
    now = time.time()
    cutoff = now - RATE_WINDOW
    request_counts[ip] = [t for t in request_counts[ip] if t > cutoff]
    if len(request_counts[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
    request_counts[ip].append(now)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)


class DreamData(BaseModel):
    text: str


def generate_interpretation(dream_text: str, budget) -> str:
    prompt = load_prompt()
    user_content = build_dream_user_message(dream_text, budget)

    message = client.messages.create(
        model=MODEL,
        max_tokens=budget.max_tokens,
        system=prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    raw = message.content[0].text

    # One rewrite only — avoids Railway/browser timeout (was 3 Claude calls).
    if violates_dreamer_address(raw):
        rewrite = client.messages.create(
            model=MODEL,
            max_tokens=budget.max_tokens,
            system=prompt,
            messages=[
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": raw},
                {"role": "user", "content": REWRITE_ADDRESS_STRICT},
            ],
        )
        raw = rewrite.content[0].text

    return raw


@app.get("/version")
async def version():
    prompt = load_prompt()
    return {
        "status": "ok",
        "prompt_sha12": prompt_sha12(),
        "address_rule": "ADDRESS" in prompt[:1500],
        "dream_ownership_rule": "DREAM OWNERSHIP" in prompt[:2000],
        "system_prompt": True,
    }


@app.post("/analyze")
async def analyze_dream(dream: DreamData, request: Request):
    check_rate_limit(request.client.host)

    try:
        validate_dream(dream.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    budget = get_response_budget(dream.text)
    try:
        raw = generate_interpretation(dream.text, budget)
    except anthropic.APIError:
        raise HTTPException(
            status_code=502,
            detail="Decode is busy. Wait a minute and try again.",
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Decode error. Try again in a moment.",
        )
    return {
        "status": "ok",
        "interpretation": raw,
        "tier": budget.tier,
        "word_limit": budget.word_limit,
        "prompt_sha12": prompt_sha12(),
    }
