"""
CivicSense – Seed script.
Creates default admin, sample authority users, sample citizens, and demo complaints.
Run: python -m backend.scripts.seed_admin
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


from backend.config import get_settings
from backend.core.security import hash_password
from backend.services.nlp_service import run_nlp_pipeline
from backend.services.urgency_service import compute_urgency
from backend.services.authority_service import get_assigned_authority

from motor.motor_asyncio import AsyncIOMotorClient


async def seed():
    """Seed the database with demo data."""
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    print("🌱 CivicSense – Seeding database...")

    # ════════════════════════════════════════════════════════
    #  1. Admin
    # ════════════════════════════════════════════════════════
    admin_email = "admin@civicsense.lk"
    existing_admin = await db.admins.find_one({"email": admin_email})
    if not existing_admin:
        await db.admins.insert_one(
            {
                "name": "System Admin",
                "email": admin_email,
                "password": hash_password("admin123"),
                "role": "admin",
                "createdAt": datetime.now(timezone.utc),
            }
        )
        print(f"  ✅ Admin created: {admin_email} / admin123")
    else:
        print(f"  ⏭️  Admin already exists: {admin_email}")

    # ════════════════════════════════════════════════════════
    #  2. Authority Users
    # ════════════════════════════════════════════════════════
    authorities_data = [
        {"name": "Water Board Officer", "email": "water@civicsense.lk", "department": "Water Board"},
        {"name": "CEB Officer", "email": "ceb@civicsense.lk", "department": "CEB"},
        {"name": "RDA Officer", "email": "rda@civicsense.lk", "department": "RDA"},
        {"name": "Municipal Officer", "email": "municipal@civicsense.lk", "department": "Municipal Council"},
        {"name": "Police Safety Officer", "email": "police@civicsense.lk", "department": "Police Safety"},
        {"name": "Disaster Mgmt Officer", "email": "disaster@civicsense.lk", "department": "Disaster Management"},
    ]

    for auth in authorities_data:
        existing = await db.authorities.find_one({"email": auth["email"]})
        if not existing:
            await db.authorities.insert_one(
                {
                    "name": auth["name"],
                    "email": auth["email"],
                    "password": hash_password("auth123"),
                    "department": auth["department"],
                    "role": "authority",
                    "createdAt": datetime.now(timezone.utc),
                }
            )
            print(f"  ✅ Authority created: {auth['email']} / auth123 ({auth['department']})")
        else:
            print(f"  ⏭️  Authority exists: {auth['email']}")

    # ════════════════════════════════════════════════════════
    #  3. Sample Citizens
    # ════════════════════════════════════════════════════════
    citizens_data = [
        {"name": "Amal Perera", "email": "amal@example.com", "phone": "0771234567", "location": "Colombo"},
        {"name": "Nisha Fernando", "email": "nisha@example.com", "phone": "0772345678", "location": "Kandy"},
        {"name": "Raj Kumar", "email": "raj@example.com", "phone": "0773456789", "location": "Galle"},
    ]

    citizen_ids = []
    for cit in citizens_data:
        existing = await db.citizens.find_one({"email": cit["email"]})
        if not existing:
            result = await db.citizens.insert_one(
                {
                    "name": cit["name"],
                    "email": cit["email"],
                    "password": hash_password("citizen123"),
                    "phone": cit["phone"],
                    "location": cit["location"],
                    "role": "citizen",
                    "createdAt": datetime.now(timezone.utc),
                }
            )
            citizen_ids.append(str(result.inserted_id))
            print(f"  ✅ Citizen created: {cit['email']} / citizen123")
        else:
            citizen_ids.append(str(existing["_id"]))
            print(f"  ⏭️  Citizen exists: {cit['email']}")

    # ════════════════════════════════════════════════════════
    #  4. Sample Complaints
    # ════════════════════════════════════════════════════════
    complaints_data = [
        {
            "description": "Severe water pipe burst on Main Street causing flooding in the entire neighborhood. "
            "Water is gushing out and damaging nearby vehicles and shop fronts. Urgent repair needed.",
            "location": "Colombo",
            "anonymous": False,
            "citizenIdx": 0,
        },
        {
            "description": "Multiple streetlights on Kandy Road have been broken for over two weeks. "
            "The area is extremely dark at night, creating a dangerous situation for pedestrians and drivers.",
            "location": "Kandy",
            "anonymous": False,
            "citizenIdx": 1,
        },
        {
            "description": "Large potholes on Galle Face Road are causing accidents. Two vehicles have already "
            "been damaged this week. The road surface is completely deteriorated and needs immediate resurfacing.",
            "location": "Galle",
            "anonymous": True,
            "citizenIdx": 2,
        },
        {
            "description": "Garbage has not been collected in our area for the past 10 days. The waste is piling up "
            "on the streets causing a terrible stench and attracting rodents. This is a health hazard.",
            "location": "Colombo",
            "anonymous": False,
            "citizenIdx": 0,
        },
        {
            "description": "A live electrical wire is dangling from a broken pole near the school entrance. "
            "Children pass by this spot every morning. This is an electrocution risk and life-threatening situation!",
            "location": "Kandy",
            "anonymous": False,
            "citizenIdx": 1,
        },
        {
            "description": "Chemical waste from the nearby factory is being dumped into the river. The water has turned "
            "dark and fish are dying. Strong chemical smell in the area. This is environmental pollution.",
            "location": "Galle",
            "anonymous": True,
            "citizenIdx": 2,
        },
        {
            "description": "Heavy flooding due to storm in our area. Roads are completely submerged and several houses "
            "have water inside. We need disaster relief and rescue operations immediately.",
            "location": "Colombo",
            "anonymous": False,
            "citizenIdx": 0,
        },
        {
            "description": "There is a gas leak near the industrial zone. Strong smell of gas in the surrounding "
            "residential area. Fire trucks have not arrived yet. This could cause an explosion.",
            "location": "Kandy",
            "anonymous": False,
            "citizenIdx": 1,
        },
    ]

    # Check if complaints already exist
    existing_count = await db.complaints.count_documents({})
    if existing_count > 0:
        print(f"  ⏭️  {existing_count} complaints already exist, skipping seed complaints.")
    else:
        for i, comp in enumerate(complaints_data):
            cit_idx = comp["citizenIdx"]
            cit_id = citizen_ids[cit_idx] if cit_idx < len(citizen_ids) else ""
            cit_name = citizens_data[cit_idx]["name"] if not comp["anonymous"] else ""

            # Run NLP pipeline
            nlp = run_nlp_pipeline(comp["description"])
            urgency_score, urgency_level = compute_urgency(
                nlp["sentiment"], nlp["confidence"], comp["description"], comp["anonymous"]
            )
            assigned = get_assigned_authority(nlp["category"], comp["description"])

            doc = {
                "description": comp["description"],
                "location": comp["location"],
                "category": nlp["category"],
                "confidence": nlp["confidence"],
                "sentiment": nlp["sentiment"],
                "urgencyScore": urgency_score,
                "urgencyLevel": urgency_level,
                "assignedAuthority": assigned,
                "departmentAssigned": False,
                "status": ["pending", "seen", "in_progress", "resolved"][i % 4],
                "anonymous": comp["anonymous"],
                "citizenId": cit_id,
                "citizenName": cit_name,
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
                "upvotes": i * 2,
                "upvotedBy": [],
                "createdAt": datetime.now(timezone.utc) - timedelta(days=7 - i),
                "updatedAt": None,
            }
            await db.complaints.insert_one(doc)
            print(
                f"  ✅ Complaint #{i+1}: {nlp['category']} → {assigned} "
                f"(Urgency: {urgency_level} {urgency_score})"
            )

    # ════════════════════════════════════════════════════════
    #  5. Sample Community
    # ════════════════════════════════════════════════════════
    comm_name = "Colombo Central Community"
    existing_comm = await db.communities.find_one({"name": comm_name})
    if not existing_comm:
        await db.communities.insert_one(
            {
                "name": comm_name,
                "description": "A community for residents of central Colombo to report and track local issues.",
                "location": "Colombo",
                "members": citizen_ids[:2] if len(citizen_ids) >= 2 else citizen_ids,
                "createdBy": "admin",
                "createdAt": datetime.now(timezone.utc),
            }
        )
        print(f"  ✅ Community created: {comm_name}")
    else:
        print(f"  ⏭️  Community exists: {comm_name}")

    client.close()
    print("\n🎉 Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
