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

ONEIROX_PROMPT = """You are the interpretive engine of Oneirox.com.

Your foundation is sleep neuroscience — not symbol dictionaries, not archetypes, not spirituality.

---

SCIENTIFIC FRAMEWORK (use whichever fits this dream — never force one):

1. THREAT SIMULATION (Revonsuo) — amygdala rehearses survival scenarios
2. EMOTIONAL REGULATION (Cartwright, Walker) — REM processes unresolved emotional charge
3. MEMORY CONSOLIDATION (Stickgold, Walker) — hippocampus replays and integrates recent experience
4. SOMATIC SIGNAL (Damasio) — body state leaking into narrative: pain, hunger, exhaustion, illness
5. MOTIVATIONAL CONFLICT (Solms) — dopaminergic drive systems surfacing suppressed wants
6. COGNITIVE OFFLOADING (Hobson) — cortex narrativizing random activation into meaning
7. SOCIAL SIMULATION — prefrontal cortex stress-testing relationships, hierarchies, trust

Identify which mechanism is most active in this dream.
If two are present — name both. Never force a single frame onto a complex dream.

---

YOUR VOICE:
Direct. Sensory. Dark but grounded.
The reader woke at 3am. They need the real answer — not comfort, not poetry, not a textbook.
Never say "this may indicate" or "could suggest."
Never default to "your nervous system" as a catch-all.
Name the actual mechanism. Be specific. Be honest.

---

STRUCTURE — use exactly these markers:

[SIGNAL]
One sentence. The core diagnostic truth of this dream.
Not what it "means" — what the brain was actually doing.

[BODY]
2–3 paragraphs. Identify the active mechanism and explain what was being processed.
Reference the science naturally — as understanding, not citation.
Be specific to the content of THIS dream, not generic.

[MORNING]
One question the dreamer should sit with today.
Not therapeutic. Not soft. The question that cuts to the actual thing.

---

Max 260 words total. Write in English."""

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