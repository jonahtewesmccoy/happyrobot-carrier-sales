# CarrierOps — Inbound Carrier Sales Automation

AI-powered inbound carrier call system for freight brokerages. Built on the HappyRobot platform with a custom backend API for load matching, carrier verification, negotiation, and real-time analytics.

## Architecture

```
Carrier calls in (web call)
         ↓
HappyRobot Voice Agent
         ↓ API tool calls
FastAPI Backend (Railway)
  ├── /api/carriers/verify/{mc}   → FMCSA verification
  ├── /api/loads/search            → Load matching
  ├── /api/calls/evaluate-offer    → Negotiation logic
  ├── /api/calls/log               → Call outcome logging
  └── /api/dashboard/metrics       → Dashboard data
         ↓
SQLite DB → Live Dashboard (/dashboard)
```

## Quick Start (Local)

```bash
# 1. Clone and enter the repo
git clone <your-repo-url>
cd happyrobot-carrier-sales

# 2. Create .env file
cp .env.example .env
# Edit .env with your API keys

# 3. Run with Docker
docker-compose up --build

# OR run directly with Python
pip install -r requirements.txt
python -c "from app.database import init_db; init_db()"
python seed_demo_calls.py  # optional: populates demo data
uvicorn app.main:app --reload

# 4. Open dashboard
open http://localhost:8000/dashboard
```

## Deploy to Railway

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and init
railway login
railway init

# 3. Set environment variables
railway variables set API_KEY=happyrobot-fde-secret-2024
railway variables set FMCSA_API_KEY=<your-fmcsa-key>

# 4. Deploy
railway up
```

Your app will be live at `https://<project>.railway.app`

## API Endpoints

All endpoints except `/health` and `/dashboard` require the header:
```
X-API-Key: <your-api-key>
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/dashboard` | Analytics dashboard |
| GET | `/api/loads/search?origin=&destination=&equipment_type=` | Search loads |
| GET | `/api/loads/{load_id}` | Get specific load |
| GET | `/api/carriers/verify/{mc_number}` | FMCSA carrier verification |
| POST | `/api/calls/evaluate-offer` | Evaluate negotiation offer |
| POST | `/api/calls/log` | Log call outcome |
| GET | `/api/dashboard/metrics` | Dashboard metrics JSON |

## HappyRobot Agent Setup

See `docs/HAPPYROBOT_AGENT_PROMPT.md` for the full agent prompt and tool configuration to paste into the HappyRobot platform.

## Tech Stack

- **Backend**: Python, FastAPI, SQLite
- **Dashboard**: Vanilla HTML/JS, Chart.js
- **Infrastructure**: Docker, Railway
- **External APIs**: FMCSA carrier verification
- **Voice Agent**: HappyRobot platform
