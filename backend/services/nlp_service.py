"""
CivicSense – NLP Service.
Uses HuggingFace Inference API for:
  1. Zero-shot classification (category)
  2. Sentiment analysis
  3. Key-phrase extraction
  4. Auto-summary
Falls back to keyword-based rules if API key is missing or the API fails.
"""

import re
import logging
from typing import Optional

import requests as http_requests

from backend.config import get_settings

logger = logging.getLogger("civicsense.nlp")

HF_API_URL = "https://api-inference.huggingface.co/models"

# ── Category labels ──────────────────────────────────────────
CATEGORIES = [
    "Water Issue",
    "Electricity Issue",
    "Road Issue",
    "Garbage Issue",
    "Safety Hazard",
    "Environmental Issue",
    "Disaster",
]

# ── Keyword fallback maps ───────────────────────────────────
KEYWORD_CATEGORY_MAP: dict[str, list[str]] = {
    "Water Issue": [
        "water", "pipe", "leak", "tap", "drain", "flood", "sewage",
        "well", "tank", "water supply", "waterlogging", "plumbing",
    ],
    "Electricity Issue": [
        "electricity", "power", "electric", "wire", "transformer",
        "blackout", "voltage", "meter", "electrocution", "power cut",
        "streetlight", "light pole",
    ],
    "Road Issue": [
        "road", "pothole", "crack", "pavement", "highway", "bridge",
        "sidewalk", "traffic", "signal", "asphalt", "speed bump",
    ],
    "Garbage Issue": [
        "garbage", "trash", "waste", "rubbish", "bin", "dump",
        "litter", "recycling", "compost", "debris", "sanitation",
    ],
    "Safety Hazard": [
        "danger", "hazard", "unsafe", "crime", "theft", "accident",
        "violence", "police", "robbery", "assault", "fire",
    ],
    "Environmental Issue": [
        "pollution", "environment", "air quality", "noise", "smoke",
        "chemical", "toxic", "deforestation", "tree", "dust", "emission",
    ],
    "Disaster": [
        "flood", "storm", "earthquake", "landslide", "tornado",
        "hurricane", "cyclone", "tsunami", "disaster", "collapse",
    ],
}

# ── Negative-sentiment keywords ─────────────────────────────
NEGATIVE_KEYWORDS = [
    "terrible", "horrible", "awful", "worst", "dangerous", "angry",
    "frustrated", "unacceptable", "disgusting", "pathetic", "urgent",
    "emergency", "critical", "broken", "damaged", "destroyed",
    "hazardous", "life-threatening", "death", "dying", "killed",
]


def _hf_headers() -> dict[str, str]:
    key = get_settings().huggingface_api_key
    if key:
        return {"Authorization": f"Bearer {key}"}
    return {}


def _has_api_key() -> bool:
    return bool(get_settings().huggingface_api_key)


# ════════════════════════════════════════════════════════════
#  1. Zero-shot Classification
# ════════════════════════════════════════════════════════════

def classify_category(text: str) -> tuple[str, float]:
    """
    Classify the complaint into a category using HF zero-shot,
    with a keyword fallback.
    Returns (category, confidence).
    """
    if _has_api_key():
        try:
            resp = http_requests.post(
                f"{HF_API_URL}/MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
                headers=_hf_headers(),
                json={
                    "inputs": text,
                    "parameters": {"candidate_labels": CATEGORIES},
                },
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                top_label = data["labels"][0]
                top_score = data["scores"][0]
                return top_label, round(top_score, 4)
            else:
                logger.warning("HF classification returned %s: %s", resp.status_code, resp.text)
        except Exception as exc:
            logger.warning("HF classification failed: %s", exc)

    # ── Keyword fallback ────────────────────────────────────
    return _keyword_classify(text)


def _keyword_classify(text: str) -> tuple[str, float]:
    """Rule-based keyword classification fallback."""
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for category, keywords in KEYWORD_CATEGORY_MAP.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > 0:
            scores[category] = count
    if scores:
        best = max(scores, key=scores.get)  # type: ignore[arg-type]
        confidence = min(scores[best] / 5.0, 0.95)
        return best, round(confidence, 4)
    return "Environmental Issue", 0.3  # default


# ════════════════════════════════════════════════════════════
#  2. Sentiment Analysis
# ════════════════════════════════════════════════════════════

def analyze_sentiment(text: str) -> float:
    """
    Return a negativity score 0-1 (1 = very negative).
    Uses HF 5-star sentiment model, maps 1-star → 1.0, 5-star → 0.0.
    Falls back to keyword scoring.
    """
    if _has_api_key():
        try:
            resp = http_requests.post(
                f"{HF_API_URL}/nlptown/bert-base-multilingual-uncased-sentiment",
                headers=_hf_headers(),
                json={"inputs": text},
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    labels = data[0] if isinstance(data[0], list) else data
                    # labels like [{"label": "1 star", "score": 0.8}, ...]
                    star_scores = {}
                    for item in labels:
                        star = int(item["label"].split()[0])
                        star_scores[star] = item["score"]
                    # Weighted average → negativity
                    weighted = sum(
                        star_scores.get(s, 0) * (5 - s) / 4 for s in range(1, 6)
                    )
                    return round(min(max(weighted, 0.0), 1.0), 4)
        except Exception as exc:
            logger.warning("HF sentiment failed: %s", exc)

    # ── Keyword fallback ────────────────────────────────────
    return _keyword_sentiment(text)


def _keyword_sentiment(text: str) -> float:
    """Keyword-based negativity score fallback."""
    text_lower = text.lower()
    hits = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)
    return round(min(hits / 5.0, 1.0), 4)


# ════════════════════════════════════════════════════════════
#  3. Key Phrase Extraction
# ════════════════════════════════════════════════════════════

def extract_keyphrases(text: str, max_phrases: int = 5) -> list[str]:
    """
    Extract key phrases using simple NLP heuristics.
    Looks for noun-phrase-like patterns.
    """
    # Remove punctuation except hyphens
    cleaned = re.sub(r"[^\w\s\-]", "", text)
    words = cleaned.split()

    # Bigrams and trigrams as candidate phrases
    candidates: list[str] = []
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
        "to", "for", "of", "and", "or", "but", "with", "by", "from",
        "this", "that", "it", "its", "my", "our", "your", "their",
        "has", "have", "had", "be", "been", "being", "i", "we", "they",
        "he", "she", "there", "here", "do", "does", "did", "not", "no",
        "very", "so", "too", "just", "about", "up", "out", "if", "as",
    }

    # Single important words
    for w in words:
        wl = w.lower()
        if len(wl) > 3 and wl not in stop_words:
            candidates.append(wl)

    # Bigrams
    for i in range(len(words) - 1):
        bg = f"{words[i]} {words[i+1]}"
        bgl = bg.lower()
        if all(w.lower() not in stop_words for w in bg.split()):
            candidates.append(bgl)

    # Score by frequency and pick top
    from collections import Counter
    freq = Counter(candidates)
    top = [phrase for phrase, _ in freq.most_common(max_phrases)]
    return top if top else ["general complaint"]


# ════════════════════════════════════════════════════════════
#  4. Auto-Summary
# ════════════════════════════════════════════════════════════

def generate_summary(text: str, max_len: int = 120) -> str:
    """Generate a short summary by extracting the most important sentence."""
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    if not sentences:
        return text[:max_len]

    # Score each sentence by keyword relevance
    all_keywords = []
    for kws in KEYWORD_CATEGORY_MAP.values():
        all_keywords.extend(kws)
    all_keywords.extend(NEGATIVE_KEYWORDS)

    best_sent = sentences[0]
    best_score = 0
    for sent in sentences:
        score = sum(1 for kw in all_keywords if kw in sent.lower())
        if score > best_score:
            best_score = score
            best_sent = sent

    summary = best_sent[:max_len]
    if len(best_sent) > max_len:
        summary += "…"
    return summary


# ════════════════════════════════════════════════════════════
#  5. Full NLP Pipeline
# ════════════════════════════════════════════════════════════

def run_nlp_pipeline(text: str) -> dict:
    """
    Run the full NLP pipeline on a complaint description.
    Returns category, confidence, sentiment, keyphrases, summary.
    """
    category, confidence = classify_category(text)
    sentiment = analyze_sentiment(text)
    keyphrases = extract_keyphrases(text)
    summary = generate_summary(text)

    return {
        "category": category,
        "confidence": confidence,
        "sentiment": sentiment,
        "keyPhrases": keyphrases,
        "summary": summary,
    }
