
---

# 🛡️ Community Safety & Digital Wellness
**Demo:** https://youtu.be/CeUhgsSzACg

**Candidate:** Pranesh Velmurugan

**Scenario:** Community Safety & Digital Wellness

**Time Investment:** 5 Hours

---

## 🚀 Quick Start

### Prerequisites

* **Python:** 3.9+
* **Node.js:** 18+
* **API Key:** Gemini API Key ([Get one here](https://aistudio.google.com/))

### Installation & Setup

```bash
# 1. Setup Backend
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Environment Configuration
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 3. Run Application
python app.py

```

### Running Tests

To ensure the environment is configured correctly, run the following:

**Backend (Pytest)**

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v

```

**Frontend (Vitest)**

```bash
cd frontend
npx vitest run

```

---

## 🤖 AI Disclosure & Verification

* **Did you use an AI assistant?** Yes (Gemini for project planning; Cursor w/ Claude Opus for execution).
* **Verification Strategy:** * **Design-First:** I authored a design document and fed it into Cursor to establish a structured plan.
* **Logic Audits:** I manually reviewed generated API routes to ensure business logic was sound and data flow was accurate.
* **Automated Testing:** I implemented test cases for both backend and frontend to prevent regression while adding new features.
* **Manual QA:** Verified all UI interactions, page transitions, and button triggers manually.



> [!IMPORTANT]
> **Rejected Suggestion:** The AI initially suggested a dummy login system using a dropdown menu of pre-set users. I rejected this as it invalidated the security-centric nature of a safety app; I insisted on a more realistic (albeit MVP) authentication flow to maintain project integrity.

---

## ⚖️ Tradeoffs & Prioritization

To stay within the **4–6 hour limit**, I focused on core functional logic over security hardening and UI polish.

| Feature Category | What was Cut (MVP) | Future Roadmap (Next Steps) |
| --- | --- | --- |
| **Communication** | Blocking in group chats | Bluetooth Mesh Network support |
| **Security** | Identity verification / Password hashing | Proper Auth & Encryption |
| **User Safety** | Real-time location sharing | Spam Avoidance & Reporting |
| **UI/UX** | High-fidelity UI styling | Push Notifications |

### Known Limitations

* **Encryption:** Group chat data is currently not encrypted.
* **Platform:** A web app is suboptimal for this use case; a native mobile app would be the ideal format for safety features.
* **Monetization:** There is currently no ad integration or revenue model.

---
