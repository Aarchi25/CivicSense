# 🏛️ CivicSense – AI-Powered Public Complaint Management System

> **Major Project & Government Portal Redesign**  
> An end-to-end intelligent civic grievance redressal and community engagement platform built entirely in Python with **FastAPI**, **Streamlit**, **MongoDB (Motor)**, and **HuggingFace NLP Models**.  
> Redesigned with prestigious government-portal aesthetics inspired by **CMC (Cuttack Municipal Corporation)**, **GIS Command Center**, and **Rail Madad Smart Classification System**.

---

## 🌟 Key Application Flow & Experiences

```
┌────────────────────────────────────────────────────────────────────────┐
│                   1. Public Home & Citizen Portal                      │
│ (CMC-Style Split Banner · Smart Ward Services · Public Ticket Tracker) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Click "Sign In" or "Register"
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   2. Dedicated IAM Authentication                      │
│    (Role Selection: 👤 Citizen  ·  🛡️ Admin  ·  🏢 Authority)         │
└───────┬───────────────────────────┼────────────────────────────┬───────┘
        │ Citizen Login             │ Admin Auth                 │ Authority Login
        ▼                           ▼                            ▼
┌───────────────────────┐   ┌────────────────────────┐   ┌────────────────────────┐
│ 3A. Citizen Dashboard │   │ 3B. GIS Admin Console  │   │ 3C. Authority Workbench│
│ • Overview & Metrics  │   │ • Trajectory Curves    │   │ • Dept Isolated Queue  │
│ • Submit Grievance    │   │ • Smart Classification │   │ • Status Transitions   │
│ • Real-time AI Diag   │   │ • Urgency Prioritize   │   │ • Inspection Notes     │
│ • Vertical Timeline   │   │ • Dept Reassignment    │   │ • Evidence Upload (IMG)│
│ • Before/After Photos │   │ • Officer & User Mgmt  │   │ • Department Analytics │
│ • AI Prompt Assistant │   │ • Bulk CSV Ingestion   │   │ • Identity Verification│
│ • Community & Feed    │   │ • Governance Reports   │   │                        │
└───────────────────────┘   └────────────────────────┘   └────────────────────────┘
```

---

## 🎨 UI/UX Design System Highlights

1. **Government Portal Aesthetic:**
   - Deep Royal Navy (`#0a2540`, `#0f3b82`, `#1d4ed8`), crisp whites, slate typography, and soft diffused shadows.
   - Clean, uncluttered layout: Streamlit default sidebar is hidden on the Public Home and Auth pages.
2. **Interactive AI Grievance Assistant:**
   - Real-time diagnostic preview that runs zero-shot classification, urgency calculation (0–100), and authority recommendation as the citizen writes.
3. **Step-by-Step Resolution Timeline (Image 5):**
   - Vertical timeline stepper with audit timestamps: **Submitted** → **Dispatched to Department** → **In Progress** → **Resolved**.
   - Side-by-side **BEFORE** (user reported) & **AFTER** (authority remediation proof) evidence photos.
4. **GIS Municipal Overview (Image 3 & 6):**
   - Service level radial gauge (`76.5% Target 75%`), citizen satisfaction rating (`4.6 / 5`), and dual-curve line charts (Pending vs In Progress trends).
5. **Smart Classification Registry (Image 7 - Rail Madad):**
   - High-density data table with AI confidence progress bars, severity chips, and instant filtering by category and status.

---

## 👥 Pre-Configured Demo Accounts

| Portal | Email | Password | Role & Scope |
| :--- | :--- | :--- | :--- |
| **Admin Console** | `admin@civicsense.lk` | `admin123` | Central administration, department reassignment, CSV ingestion |
| **Water Board** | `water@civicsense.lk` | `auth123` | Water pipeline leaks, flooding, sewage defects |
| **Electricity (CEB)** | `ceb@civicsense.lk` | `auth123` | Power cuts, sparking transformers, dangling live wires |
| **Roads (RDA)** | `rda@civicsense.lk` | `auth123` | Potholes, road damage, traffic signal defects |
| **Municipal Council** | `municipal@civicsense.lk` | `auth123` | Garbage collection, public sanitation, canal cleaning |
| **Police Safety** | `police@civicsense.lk` | `auth123` | Street hazards, public security, accidents |
| **Disaster Mgmt** | `disaster@civicsense.lk` | `auth123` | Landslides, severe monsoon flooding, cyclones |
| **Citizen** | `amal@example.com` | `citizen123` | Pre-registered citizen account *(or register a new account)* |

---

## 🚀 How to Run the Application

### 1. Ensure Dependencies & Database
```bash
# Install dependencies
pip install -r requirements.txt

# Seed the database with demo accounts and sample complaints
python -m backend.scripts.seed_admin
```

### 2. Start the Backend API Server
```bash
# Start FastAPI backend (port 8000)
uvicorn backend.main:app --reload --port 8000
```
- Interactive API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

To create a bootstrap admin automatically at backend startup, set these values in
`.env` before starting the API:

```env
BOOTSTRAP_ADMIN_NAME=CivicSense Admin
BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_PASSWORD=replace-with-a-strong-password
```

The bootstrap runs after MongoDB connects. It creates the configured email only
when that email is not already in the `admins` collection; it does not change
existing admin accounts. If both the email and password are unset, bootstrap is
skipped.

To test admin login, open `/docs`, expand **POST /api/admin/login**, select **Try
it out**, and submit the bootstrap email and password:

```json
{
  "email": "admin@example.com",
  "password": "replace-with-a-strong-password"
}
```

A successful login returns an access token and admin details. If login returns
401, confirm the `.env` values and restart the backend.

### 3. Start the Streamlit Frontend
```bash
# Start Streamlit application (port 8501)
streamlit run frontend/app.py
```
- Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📁 Project Architecture & File Structure

```
CivicPulse/
├── backend/
│   ├── core/security.py         # JWT tokens & native bcrypt password verification
│   ├── models/schemas.py        # Pydantic v2 schemas
│   ├── routers/
│   │   ├── admin.py             # Admin endpoints, department reassignment & CSV upload
│   │   ├── auth.py              # Citizen, admin, and authority login/registration
│   │   ├── authority.py         # Department queue, status update, evidence upload
│   │   ├── community.py         # Neighborhood feed & announcements
│   │   ├── complaints.py        # Submission, AI preview, public tracking, identity reveal
│   │   └── stats.py             # Analytical aggregates & historical trends
│   ├── services/
│   │   ├── authority_service.py # Smart department routing logic
│   │   ├── nlp_service.py       # DeBERTa zero-shot + keyword fallback pipeline
│   │   └── urgency_service.py   # Multi-factor urgency engine (0–100 score)
│   ├── config.py                # Pydantic-settings configuration
│   ├── database.py              # Motor async MongoDB driver & index lifecycle
│   └── main.py                  # FastAPI factory, CORS, static uploads
├── frontend/
│   ├── components/ui.py         # Gov portal UI components (timeline, gauge, cards)
│   ├── pages/
│   │   ├── public_home.py       # CMC-inspired public landing page & quick tracker
│   │   ├── auth_page.py         # Dedicated role-based login & registration
│   │   ├── citizen_dashboard.py # 8-section Citizen portal with live AI preview & tracker
│   │   ├── admin_dashboard.py   # GIS & Rail Madad admin management console
│   │   └── authority_dashboard.py # Department-isolated operations & evidence upload
│   ├── styles/custom.css        # Professional government design tokens & styling
│   ├── api_client.py            # Requests wrapper for backend REST API
│   └── app.py                   # Main Streamlit router (Home → Auth → Dashboard)
├── requirements.txt             # Pinned package dependencies
└── README.md                    # Project documentation
```
