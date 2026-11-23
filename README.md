# 🏙️ CivicSense – Intelligent Civic Complaint Management System

CivicSense is an intelligent civic complaint management platform designed to streamline the reporting, classification, tracking, and resolution of public grievances. It leverages AI-based classification and urgency detection to improve complaint handling and coordination between citizens, authorities, and administrators.

## ✨ Key Features

- 👤 **Citizen Portal:** Register, submit, and track civic complaints.
- 🏢 **Authority Portal:** Manage assigned complaints and update resolution statuses.
- 🛡️ **Admin Portal:** Manage users, authorities, departments, and complaints.
- 🤖 **AI-Based Classification:** Automatically identifies complaint categories and relevant departments using zero-shot classification.
- 🚨 **Urgency Detection:** Evaluates complaint priority through keyword-based scoring and sentiment analysis.
- 📊 **Complaint Tracking:** Maintains complaint status and resolution history.
- 🔐 **Secure Authentication:** JWT-based authentication with role-based access control and Bcrypt password hashing.
- 📩 **Notifications:** Keeps users informed about complaint progress.

## 🛠️ Technology Stack

| Component | Technologies |
|---|---|
| Frontend | Streamlit, Custom CSS |
| Backend | Python, FastAPI |
| Database | MongoDB Atlas, Motor |
| AI/ML | Hugging Face Transformers, DeBERTa |
| Authentication | JWT, Bcrypt |
| API Documentation | Swagger UI (OpenAPI) |
| Development Tools | VS Code, Git, GitHub |

## 🧠 AI Implementation

CivicSense integrates AI to minimize manual effort in complaint processing.

- **Zero-Shot Classification:** Uses a pretrained DeBERTa-based model to classify complaints and identify relevant departments without task-specific model training.
- **Urgency Assessment:** Combines predefined keyword weights and sentiment analysis to calculate an urgency index and support complaint prioritization.

## 🔄 System Workflow

1. 👤 Citizens register and log in.
2. 📝 Complaints are submitted with relevant details.
3. 🤖 AI analyzes complaints and predicts categories and departments.
4. 🚨 The system evaluates complaint urgency.
5. 🏢 Complaints are routed to the relevant authorities.
6. 🔄 Authorities update complaint status and resolution progress.
7. 📊 Administrators monitor the overall complaint management process.

## 📁 Project Structure

```text
CivicSense/
│
├── backend/
│   ├── main.py
│   ├── models/
│   ├── routers/
│   ├── core/
│   └── services/
│
├── frontend/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## ⚙️ Installation & Setup

**1. Clone the repository**

```bash
git clone <repository-url>
cd CivicSense
```

**2. Create and activate a virtual environment**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Create a `.env` file using `.env.example` and provide the required configuration, including MongoDB connection details and authentication credentials.

**5. Start the backend**

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

**6. Start the frontend**

```bash
streamlit run <frontend-entry-file>
```

## 📡 API Documentation

FastAPI provides interactive API documentation through Swagger UI.

🔗 **Swagger UI:** `http://127.0.0.1:8000/docs`

## ⚠️ Limitations

- Classification may be less accurate for unusual or ambiguous complaints.
- Urgency scoring relies on predefined keyword weights and sentiment rules.
- Complaint categories and departments are predefined.
- Prediction accuracy depends on the language and clarity of submitted complaints.

## 🚀 Future Scope

- 🌐 Multilingual complaint processing.
- 🧠 Enhanced urgency prediction using trained ML models.
- 🔔 Real-time notifications and complaint updates.
- 🗺️ Geographic complaint visualization and analytics.
- 🏛️ Integration with government grievance management systems.

## 🎯 Project Objective

To make civic grievance management more accessible, transparent, and efficient through AI-powered classification, automated prioritization, and streamlined coordination between citizens and authorities.