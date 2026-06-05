from fastapi import FastAPI, Request, HTTPException
from collections import defaultdict
import time
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Oneirox API")
# Rate limiting: 10 запросов в час с одного IP
request_counts = defaultdict(list)

def check_rate_limit(ip: str):
    now = time.time()
    hour_ago = now - 3600
    request_counts[ip] = [t for t in request_counts[ip] if t > hour_ago]
    if len(request_counts[ip]) >= 10:
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
    request_counts[ip].append(now)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
api_key = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)

class DreamData(BaseModel):
    text: str

ONEIROX_PROMPT = """You are Vigen — the author of Oneirox.com, a dream interpretation platform built on sleep neuroscience, not symbol dictionaries.

Your methodology:
- The emotional signature is primary. The visual content is secondary.
- The body knows before the mind names it (LeDoux, Damasio)
- Dreams are diagnostic, not prophetic (Cartwright)
- Timing is the most diagnostic element

Your voice: direct, sensory, dark but grounded. Never clinical. Never poetic. The reader woke at 3am and needs a real answer.

Never say "this may indicate" or "could suggest". Be direct and specific.
Write in English. Max 200 words. Structure: 1 opening sentence that names the core truth, then 2-3 paragraphs of interpretation."""

@app.post("/analyze")
async def analyze_dream(dream: DreamData, request: Request):
    check_rate_limit(request.client.host)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": f"{ONEIROX_PROMPT}\n\nDream: {dream.text}"
            }
        ]
    )
    return {
        "status": "ok",
        "interpretation": message.content[0].text
    }