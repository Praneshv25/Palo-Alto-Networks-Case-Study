import os
import json
from google import genai

SYSTEM_PROMPT = """You are a community safety analyst for a neighborhood safety platform. Given a raw neighborhood post, your job is to transform it from emotional "noise" into calm, actionable "signal."

Instructions:
1. Extract only verified facts. Remove rumors, insults, panic language, and toxic commentary.
2. Rewrite the information in a calm, neutral tone (max 3 sentences) as "summary".
3. Create a concise "title" — a calm headline of max 10 words.
4. Classify the report:
   - category: "Local_Physical" (fires, break-ins, hazards, weather) or "Digital_Security" (phishing, scams, hacking, malware)
   - severity: "Low", "Medium", or "High"
5. Provide exactly 3 concrete, actionable steps the reader can take immediately as "checklist".

Return ONLY valid JSON with no markdown formatting, no code fences:
{"title": "...", "summary": "...", "severity": "...", "category": "...", "checklist": ["...", "...", "..."]}"""


_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        _client = genai.Client(api_key=api_key)
    return _client


def filter_with_ai(content):
    """Send raw post content to Gemini and return structured safety report fields."""
    client = _get_client()

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"Raw neighborhood post:\n\n{content}",
        config={
            "system_instruction": SYSTEM_PROMPT,
            "temperature": 0.3,
        },
    )

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    result = json.loads(text)

    required = {"title", "summary", "severity", "category", "checklist"}
    if not required.issubset(result.keys()):
        raise ValueError(f"Missing fields in AI response: {required - result.keys()}")

    if result["severity"] not in ("Low", "Medium", "High"):
        raise ValueError(f"Invalid severity: {result['severity']}")
    if result["category"] not in ("Local_Physical", "Digital_Security"):
        raise ValueError(f"Invalid category: {result['category']}")
    if not isinstance(result["checklist"], list) or len(result["checklist"]) < 1:
        raise ValueError("Checklist must be a non-empty list")

    return result
