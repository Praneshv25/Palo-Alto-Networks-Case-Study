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

AGGREGATE_PROMPT = """You are a community safety analyst. A new neighborhood post has come in. Compare it with an existing safety report to determine if they describe the SAME real-world incident (same location, same event type, happening around the same time).

Existing report:
Title: {existing_title}
Summary: {existing_summary}

New post:
{new_content}

If they describe the SAME incident, produce a merged report that combines all useful details from both. The merged summary should be calm, factual, and no longer than 3 sentences. Keep the most specific location information available.

Respond with ONLY valid JSON, no markdown, no code fences:

If same incident:
{{"same_incident": true, "title": "...", "summary": "...", "severity": "...", "checklist": ["...", "...", "..."]}}

If different incidents:
{{"same_incident": false}}"""


_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        _client = genai.Client(api_key=api_key)
    return _client


def _parse_and_strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return text


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

    result = json.loads(_parse_and_strip_fences(response.text))

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


def check_and_aggregate(existing_title, existing_summary, new_content):
    """
    Ask Gemini if new_content describes the same incident as the existing report.
    Returns {"same_incident": False} or {"same_incident": True, "title": ..., "summary": ..., "severity": ..., "checklist": [...]}.
    """
    client = _get_client()

    prompt = AGGREGATE_PROMPT.format(
        existing_title=existing_title,
        existing_summary=existing_summary,
        new_content=new_content,
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={"temperature": 0.2},
    )

    result = json.loads(_parse_and_strip_fences(response.text))

    if not isinstance(result.get("same_incident"), bool):
        raise ValueError("Missing 'same_incident' boolean in aggregation response")

    if result["same_incident"]:
        required = {"title", "summary", "severity", "checklist"}
        if not required.issubset(result.keys()):
            raise ValueError(f"Missing merged fields: {required - result.keys()}")
        if result["severity"] not in ("Low", "Medium", "High"):
            raise ValueError(f"Invalid severity in merge: {result['severity']}")
        if not isinstance(result["checklist"], list) or len(result["checklist"]) < 1:
            raise ValueError("Merged checklist must be a non-empty list")

    return result
