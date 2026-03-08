import re

HIGH_KEYWORDS = ["robbery", "breach", "fire", "shooting", "flood", "armed", "evacuation", "assault", "stabbing", "explosion"]
MEDIUM_KEYWORDS = ["theft", "scam", "phishing", "suspicious", "outage", "break-in", "vandalism", "accident"]
LOW_KEYWORDS = ["noise", "pothole", "graffiti", "litter", "parking"]

DIGITAL_KEYWORDS = {"phishing", "breach", "scam", "hack", "password", "malware", "ransomware", "spyware"}

STOP_WORDS = {
    "a", "an", "the", "is", "in", "on", "at", "of", "to", "and", "or",
    "was", "has", "been", "are", "were", "it", "i", "my", "we", "you",
    "for", "with", "from", "by", "not", "no", "this", "that", "there",
    "here", "just", "very", "be", "s", "please", "someone", "some",
}

SEVERITY_RANK = {"Low": 0, "Medium": 1, "High": 2}

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


def _build_title(content, matched_keyword):
    """Build a concise title from the raw content, up to 10 words."""
    # Capitalize and trim to a reasonable headline length
    stripped = content.strip().rstrip(".,!?")
    words = stripped.split()
    if len(words) <= 10:
        title = stripped.capitalize()
    else:
        title = " ".join(words[:10]).capitalize() + "…"
    return title


def _build_summary(content, matched_keyword):
    """Build a factual summary using the original post content."""
    # Use the first ~250 chars of cleaned content as the base
    cleaned = re.sub(r'\s+', ' ', content.strip())
    excerpt = cleaned[:250].rstrip(" .,!?")
    if len(cleaned) > 250:
        excerpt += "…"
    return (
        f"{excerpt}. "
        "This report has been flagged for community awareness and is pending verification."
    )


def _significant_words(text):
    """Return the set of meaningful lowercase words from text."""
    return {
        w for w in re.findall(r'\b[a-z]+\b', text.lower())
        if w not in STOP_WORDS and len(w) > 2
    }


def jaccard_similarity(text_a, text_b):
    """Word-overlap (Jaccard) similarity between two strings, in [0, 1]."""
    a = _significant_words(text_a)
    b = _significant_words(text_b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def fallback_merge(existing_report, new_content):
    """
    Rule-based merge of a new post into an existing report dict.
    Returns updated title/summary/severity/checklist.
    Keeps the existing title; escalates severity if the new post is worse;
    appends new location/detail to the summary if distinct.
    """
    new_analysis = analyze_with_fallback(new_content)

    # Escalate severity to the worse of the two
    existing_rank = SEVERITY_RANK.get(existing_report["severity"], 0)
    new_rank = SEVERITY_RANK.get(new_analysis["severity"], 0)
    merged_severity = existing_report["severity"] if existing_rank >= new_rank else new_analysis["severity"]

    # Append new content only when it adds location/detail not already present
    existing_summary = existing_report["summary"]
    new_excerpt = new_content.strip()[:180].rstrip(" .,!?")
    if new_excerpt.lower() not in existing_summary.lower():
        merged_summary = (
            f"{existing_summary} "
            f"Additional report: {new_excerpt}."
        )
    else:
        merged_summary = existing_summary

    return {
        "title": existing_report["title"],
        "summary": merged_summary,
        "severity": merged_severity,
        "checklist": new_analysis["checklist"],
    }


def news_matches_report(article_title, article_content, report_title, report_summary, threshold=0.2):
    """
    Rule-based check: does a news article likely cover the same incident as a report?
    Uses Jaccard similarity across all four text fields combined.
    """
    article_text = article_title + " " + article_content
    report_text = report_title + " " + report_summary
    return jaccard_similarity(article_text, report_text) >= threshold


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
        matched_keyword = "incident"

    is_digital = any(kw in content_lower for kw in DIGITAL_KEYWORDS)
    category = "Digital_Security" if is_digital else "Local_Physical"
    checklist = DIGITAL_CHECKLISTS if is_digital else LOCAL_CHECKLISTS

    return {
        "title": _build_title(content, matched_keyword),
        "summary": _build_summary(content, matched_keyword),
        "severity": severity,
        "category": category,
        "checklist": checklist,
    }
