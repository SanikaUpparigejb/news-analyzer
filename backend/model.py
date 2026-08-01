import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ── Client setup ───────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment. Add it to backend/.env")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL  = "gemini-2.5-flash"

print(f"Gemini client initialised. Model: {MODEL}")

TOPICS = [
    "politics", "technology", "sports",
    "business", "health", "science",
    "entertainment", "environment"
]


# ── Core analysis function ─────────────────────────────────────────────────────

def analyze_article(text: str) -> dict:
    """
    Single Gemini API call that performs all three tasks simultaneously:
      - Abstractive summarization
      - Topic classification with confidence scores
      - Sentiment analysis

    Returning all three from one call is more efficient than three separate
    API calls — one round trip, one billing unit, lower total latency.
    We instruct the model to return structured JSON so we can parse it
    reliably without any regex or text post-processing.
    """

    prompt = f"""
You are a news article analysis assistant. Analyze the article below and return
a JSON object with exactly this structure — no markdown, no code fences, 
no explanation, just the raw JSON:

{{
  "summary": "A 3-4 sentence abstractive summary in your own words. Do not copy 
               sentences from the article. Capture the key facts and context.",
  "topic": {{
    "top_topic": "the single most relevant topic from this list: {TOPICS}",
    "confidence": 85.5,
    "all_scores": {{
      "politics": 10.2,
      "technology": 85.5,
      "sports": 0.1,
      "business": 3.1,
      "health": 0.5,
      "science": 0.4,
      "entertainment": 0.1,
      "environment": 0.1
    }}
  }},
  "sentiment": {{
    "sentiment": "Positive",
    "confidence": 92.3
  }}
}}

Rules:
- summary must be 3-4 sentences, genuinely abstractive, not copied from the text
- top_topic must be exactly one value from: {TOPICS}
- all_scores values must be floats that sum to 100.0
- sentiment must be exactly "Positive" or "Negative"
- confidence values are floats between 0.0 and 100.0
- return only valid JSON, nothing else

Article:
{text}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,   # low temperature = more consistent, factual output
            max_output_tokens=1024,
        )
    )

    raw = response.text.strip()

    # Strip markdown code fences if the model wraps output despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)


# ── Public interface (matches the signatures main.py expects) ─────────────────
# main.py calls summarize(), classify_topic(), and analyze_sentiment() separately.
# We cache the full Gemini response on the first call and return the relevant
# parts for the next two calls — so we only hit the API once per article
# regardless of call order.

_cache: dict = {}   # keyed by hash of article text


def _get_analysis(text: str) -> dict:
    """Return cached analysis or call Gemini and cache the result."""
    key = hash(text)
    if key not in _cache:
        _cache[key] = analyze_article(text)
    return _cache[key]


def summarize(text: str) -> str:
    return _get_analysis(text)["summary"]


def classify_topic(text: str) -> dict:
    return _get_analysis(text)["topic"]


def analyze_sentiment(text: str) -> dict:
    return _get_analysis(text)["sentiment"]


def clear_cache():
    """Call this if memory becomes a concern during long server uptime."""
    _cache.clear()