"""
CivicSense – CSV bulk-import service.
Processes uploaded CSV files: validates rows, runs the full AI pipeline
on each, and inserts complaints into MongoDB.
"""

import csv
import io
import logging
from datetime import datetime, timezone

from backend.database import get_db
from backend.services.nlp_service import run_nlp_pipeline
from backend.services.urgency_service import compute_urgency
from backend.services.authority_service import get_assigned_authority

logger = logging.getLogger("civicsense.csv")


async def process_csv(
    file_content: bytes,
    admin_id: str,
) -> dict:
    """
    Parse a CSV with columns: text, location, timestamp.
    Run each row through the NLP pipeline and insert into DB.
    Returns {"imported": N, "errors": [...]}.
    """
    db = get_db()
    errors: list[dict] = []
    imported = 0

    try:
        decoded = file_content.decode("utf-8")
    except UnicodeDecodeError:
        decoded = file_content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(decoded))

    # Validate header
    required_cols = {"text", "location", "timestamp"}
    if not reader.fieldnames or not required_cols.issubset(
        {c.strip().lower() for c in reader.fieldnames}
    ):
        return {
            "imported": 0,
            "errors": [
                {
                    "row": 0,
                    "message": f"CSV must have columns: {', '.join(required_cols)}. "
                    f"Found: {reader.fieldnames}",
                }
            ],
        }

    # Normalise field names
    field_map = {}
    for fn in reader.fieldnames:
        field_map[fn] = fn.strip().lower()

    for row_num, row in enumerate(reader, start=2):
        # Normalise keys
        norm = {field_map.get(k, k.strip().lower()): (v or "").strip() for k, v in row.items()}
        text = norm.get("text", "")
        location = norm.get("location", "")
        timestamp_str = norm.get("timestamp", "")

        # ── Validation ──────────────────────────────────────
        if not text or len(text) < 10:
            errors.append({"row": row_num, "message": "Text too short (min 10 chars)"})
            continue
        if not location:
            errors.append({"row": row_num, "message": "Location is empty"})
            continue

        # Parse timestamp
        created_at = datetime.now(timezone.utc)
        if timestamp_str:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%Y %H:%M"):
                try:
                    created_at = datetime.strptime(timestamp_str, fmt).replace(
                        tzinfo=timezone.utc
                    )
                    break
                except ValueError:
                    continue

        # ── NLP Pipeline ────────────────────────────────────
        try:
            nlp = run_nlp_pipeline(text)
            urgency_score, urgency_level = compute_urgency(
                nlp["sentiment"], nlp["confidence"], text, anonymous=True
            )
            assigned = get_assigned_authority(nlp["category"], text)

            doc = {
                "description": text,
                "location": location,
                "category": nlp["category"],
                "confidence": nlp["confidence"],
                "sentiment": nlp["sentiment"],
                "urgencyScore": urgency_score,
                "urgencyLevel": urgency_level,
                "assignedAuthority": assigned,
                "status": "pending",
                "anonymous": True,
                "citizenId": "",
                "citizenName": "",
                "imagePath": None,
                "summary": nlp["summary"],
                "keyPhrases": nlp["keyPhrases"],
                "notes": [],
                "identityRequest": {
                    "status": "none",
                    "requestedBy": "",
                    "requestedAt": None,
                    "respondedAt": None,
                },
                "upvotes": 0,
                "upvotedBy": [],
                "importedBy": admin_id,
                "createdAt": created_at,
                "updatedAt": None,
            }
            await db.complaints.insert_one(doc)
            imported += 1

        except Exception as exc:
            logger.error("CSV row %d failed: %s", row_num, exc)
            errors.append({"row": row_num, "message": str(exc)})

    return {"imported": imported, "errors": errors}
