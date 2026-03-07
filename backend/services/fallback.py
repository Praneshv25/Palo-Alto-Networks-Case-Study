import re

HIGH_KEYWORDS = ["robbery", "breach", "fire", "shooting", "flood", "armed", "evacuation"]
MEDIUM_KEYWORDS = ["theft", "scam", "phishing", "suspicious", "outage"]
LOW_KEYWORDS = ["noise", "pothole", "graffiti", "litter"]

DIGITAL_KEYWORDS = {"phishing", "breach", "scam", "hack", "password", "malware", "ransomware", "spyware"}

LOCAL_CHECKLISTS = [
    "Stay clear of the affected area and follow local authority instructions.",
    "Contact emergency services (911) if the situation is ongoing.",
    "Check on neighbors who may need assistance.",
]

DIGITAL_CHECKLISTS = [
    "Do not click suspicious links or provide personal information.",
    "Change passwords for affected accounts immediately.",
    "Report the incident to local cybersecurity resources or your IT department.",
]


def analyze_with_fallback(content):
    """Rule-based fallback when Gemini is unavailable."""
    content_lower = content.lower()

    severity = "Low"
    matched_keyword = None

    for kw in HIGH_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', content_lower):
            severity = "High"
            matched_keyword = kw
            break

    if matched_keyword is None:
        for kw in MEDIUM_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', content_lower):
                severity = "Medium"
                matched_keyword = kw
                break

    if matched_keyword is None:
        for kw in LOW_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', content_lower):
                matched_keyword = kw
                break

    if matched_keyword is None:
        matched_keyword = "activity"

    is_digital = any(kw in content_lower for kw in DIGITAL_KEYWORDS)
    category = "Digital_Security" if is_digital else "Local_Physical"
    checklist = DIGITAL_CHECKLISTS if is_digital else LOCAL_CHECKLISTS

    title = f"Flagged Activity: {matched_keyword.title()}"
    summary = (
        f"Potential {matched_keyword} reported by a community member. "
        "AI analysis is currently unavailable. This report is pending manual verification."
    )

    return {
        "title": title,
        "summary": summary,
        "severity": severity,
        "category": category,
        "checklist": checklist,
    }
