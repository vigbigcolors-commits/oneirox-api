from fastapi import FastAPI, Request, HTTPException
from collections import defaultdict
from pathlib import Path
import time
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import os
from dotenv import load_dotenv

from dream_validation import build_user_message, get_response_budget, sanitize_decode_output, validate_dream

load_dotenv()

app = FastAPI(title="Oneirox API")
# Rate limiting: 5 запросов в час с одного IP
request_counts = defaultdict(list)
RATE_LIMIT = 5
RATE_WINDOW = 3600

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

PROMPT_PATH = Path(__file__).resolve().parent / "ONEIROX_PROMPT.txt"
ONEIROX_PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip()

@app.post("/analyze")
async def analyze_dream(dream: DreamData, request: Request):
    check_rate_limit(request.client.host)

    try:
        mode = validate_dream(dream.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    budget = get_response_budget(dream.text, mode)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=budget.max_tokens,
        messages=[
            {
                "role": "user",
                "content": build_user_message(ONEIROX_PROMPT, dream.text, budget, mode),
            }
        ],
    )
    raw = sanitize_decode_output(message.content[0].text)
    return {
        "status": "ok",
        "interpretation": raw,
        "tier": budget.tier,
        "mode": mode,
        "word_limit": budget.word_limit,
    }
