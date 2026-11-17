"""
CivicSense – Authority mapping service.
Maps complaint categories to the responsible government authority.
"""

# ── Category → Authority department mapping ─────────────────
CATEGORY_AUTHORITY_MAP: dict[str, str] = {
    "Water Issue": "Water Board",
    "Electricity Issue": "CEB",
    "Road Issue": "RDA",
    "Garbage Issue": "Municipal Council",
    "Safety Hazard": "Police Safety",
    "Environmental Issue": "Municipal Council",
    "Disaster": "Disaster Management",
}

# ── Extra keyword overrides for edge cases ──────────────────
KEYWORD_OVERRIDES: dict[str, str] = {
    "flood": "Disaster Management",
    "storm": "Disaster Management",
    "cyclone": "Disaster Management",
    "earthquake": "Disaster Management",
    "landslide": "Disaster Management",
    "tsunami": "Disaster Management",
    "tornado": "Disaster Management",
}


def get_assigned_authority(category: str, text: str = "") -> str:
    """
    Determine which authority department handles this complaint.
    First checks keyword overrides (disaster-related), then uses the category map.
    """
    text_lower = text.lower()
    for keyword, authority in KEYWORD_OVERRIDES.items():
        if keyword in text_lower:
            return authority

    return CATEGORY_AUTHORITY_MAP.get(category, "Municipal Council")


def get_all_departments() -> list[str]:
    """Return list of all known authority departments."""
    return list(set(CATEGORY_AUTHORITY_MAP.values()) | {"Disaster Management"})
