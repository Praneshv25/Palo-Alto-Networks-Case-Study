# Community Guardian

A digital wellness and safety platform that transforms noisy neighborhood posts into verified, calm safety reports using AI-powered "Noise-to-Signal" filtering.

## Architecture

```
┌─────────────────┐       ┌──────────────────────────────────────┐
│  React Frontend │──────▶│          Flask Backend               │
│  (TypeScript)   │  API  │                                      │
│                 │◀──────│  ┌────────────┐   ┌──────────────┐  │
│  - Signal Feed  │       │  │ Gemini 3   │   │  Rule-Based  │  │
│  - Report Form  │       │  │ Flash AI   │   │  Fallback    │  │
│  - Safe Circle  │       │  └─────┬──────┘   └──────┬───────┘  │
│  - Vote System  │       │        │                  │          │
└─────────────────┘       │        ▼                  ▼          │
                          │  ┌─────────────────────────────┐     │
                          │  │    SQLite (guardian.db)      │     │
                          │  │  Users │ RawPosts │ Reports  │     │
                          │  │  SafeCircles │ Votes         │     │
                          │  └─────────────────────────────┘     │
                          └──────────────────────────────────────┘
```

**Tech Stack**: React + TypeScript + Vite (frontend) | Flask + Python (backend) | SQLite (data) | Gemini 2.0 Flash (AI) | Tailwind CSS (styling)

## Features

- **Noise-to-Signal AI Filtering** — Transforms emotional, panicked posts into calm, factual reports with actionable 1-2-3 checklists via Gemini
- **Dual-Tab Feed** — Local Safety and Digital Defense categories with keyword search and severity/status filters
- **Rule-Based Fallback** — Keyword/regex engine activates when Gemini is unavailable, tagging reports as "Pending Verification"
- **Community-Driven Truth** — Up/down voting system with trust badge lifecycle (AI Generated → Community Verified / Flagged)
- **Status Resolution** — Mark reports as "Resolved" for visual closure and anxiety reduction
- **Safe Circle** — Share safety status with trusted contacts (prototype with synthetic data)
- **Calm UI** — De-saturated blue/green palette designed to reduce alert fatigue

## Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- A Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env from the example
cp .env.example .env
# Edit .env and add your Gemini API key

python app.py
# Server runs on http://localhost:5000
```

The database is created and seeded automatically on first run.

### Frontend

```bash
cd frontend
npm install
npm run dev
# App runs on http://localhost:5173
```

The Vite dev server proxies `/api` requests to the Flask backend on port 5000.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | API + AI connectivity status |
| `GET` | `/api/reports` | List reports (query: `category`, `search`, `status`, `severity`) |
| `POST` | `/api/reports` | Create report from raw post via AI filtering |
| `PATCH` | `/api/reports/<id>` | Update report status (Active/Resolved) |
| `POST` | `/api/reports/<id>/vote` | Cast/toggle/switch a vote on a report |
| `GET` | `/api/users` | List synthetic users |

### POST /api/reports

```json
{
  "content": "OMG fire near the park everyone run!!!",
  "category": "local",
  "author_id": "user_002"
}
```

### POST /api/reports/:id/vote

```json
{
  "user_id": "user_001",
  "vote_type": "up"
}
```

## Trust Label Lifecycle

Reports move through a trust lifecycle based on community voting:

- **AI Generated** — Default for Gemini-processed reports
- **Pending Verification** — Default for fallback (non-AI) reports
- **Community Verified** — 3+ upvotes with upvotes > 2× downvotes
- **Flagged** — 3+ downvotes exceeding upvotes

## Running Tests

### Backend (17 tests)

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

Covers: AI happy path, fallback on failure, input validation, voting logic, trust badge transitions.

### Frontend (11 tests)

```bash
cd frontend
npx vitest run
```

Covers: ReportCard rendering, severity badges, trust badge states, vote display, resolved status.

## Data Safety

- All data is **synthetic** — no real personal information
- API keys managed via `.env` (never committed)
- Location uses **neighborhood-level** geofencing, not GPS coordinates
- Safe Circle concept uses **encrypted sharing** (visual prototype)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key for AI filtering |
