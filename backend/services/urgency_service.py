"""
CivicSense – Urgency scoring service.

Formula:
  urgency = (sentiment × 0.3) + (confidence × 0.2) + (hazard_keyword × 0.4) + (trust × 0.1)

Levels:
  Critical  >= 0.9
  Urgent    >= 0.7
  Normal    <  0.7
"""

import re

# ── Hazard keywords with severity weights ────────────────────
HAZARD_KEYWORDS: dict[str, float] = {
    # Extreme (1.0)
    "fire": 1.0,
    "electrocution": 1.0,
    "explosion": 1.0,
    "gas leak": 1.0,
    "collapse": 1.0,
    "death": 1.0,
    "killed": 1.0,
    "life-threatening": 1.0,
    # High (0.85)
    "flood": 0.85,
    "landslide": 0.85,
    "earthquake": 0.85,
    "tornado": 0.85,
    "cyclone": 0.85,
    "tsunami": 0.85,
    "drowning": 0.85,
    # Moderate-High (0.7)
    "accident": 0.7,
    "injury": 0.7,
    "toxic": 0.7,
    "chemical": 0.7,
    "contamination": 0.7,
    "electrical fault": 0.7,
    "live wire": 0.7,
    "sinkhole": 0.7,
    # Moderate (0.5)
    "danger": 0.5,
    "hazard": 0.5,
    "unsafe": 0.5,
    "broken": 0.5,
    "damaged": 0.5,
    "emergency": 0.5,
    "urgent": 0.5,
    "critical": 0.5,
    # Low (0.3)
    "pothole": 0.3,
    "blocked": 0.3,
    "overflow": 0.3,
    "clogged": 0.3,
    "crack": 0.3,
}


def _compute_hazard_score(text: str) -> float:
    """Return the highest matching hazard keyword severity."""
    text_lower = text.lower()
    max_score = 0.0
    for keyword, severity in HAZARD_KEYWORDS.items():
        if keyword in text_lower:
            max_score = max(max_score, severity)
    return max_score


def compute_urgency(
    sentiment: float,
    confidence: float,
    text: str,
    anonymous: bool,
) -> tuple[float, str]:
    """
    Compute urgency score and level.
    Returns (score, level_string).
    """
    hazard = _compute_hazard_score(text)
    trust = 0.3 if anonymous else 0.8

    score = (
        sentiment * 0.3
        + confidence * 0.2
        + hazard * 0.4
        + trust * 0.1
    )
    score = round(min(score, 1.0), 4)

    if score >= 0.9:
        level = "Critical"
    elif score >= 0.7:
        level = "Urgent"
    else:
        level = "Normal"

    return score, level
