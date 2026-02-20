# FraudX

**FraudX** is a full-stack fraud and money-mule detection platform. Upload transaction CSV data, run forensic analysis on the backend, and explore suspicious accounts and fraud rings in an interactive graph (2D Sigma.js or 3D) on the frontend .

---

## Features

- **CSV upload & validation** — Transaction data with required columns; frontend parses CSV to build the full graph; backend validates and runs detection.
- **Forensic analysis** — Cycle detection, smurfing, shell-chain, and velocity-based algorithms; configurable thresholds via environment variables.
- **Interactive graph** — 2D (Sigma.js) or 3D view; all nodes from your CSV; color by suspicion score (min–max); green for non-fraud; zoom, pan, click to select and highlight edges.
- **Fraud rings & scores** — Suspicious accounts, ring membership, risk scores; export JSON (suspicious_accounts, fraud_rings, summary).

---

## Video demo & links

| Resource | URL |
|----------|-----|
| **Video demo** | _Add your video URL here (e.g. YouTube, Loom)_ |
| **Live app** | https://fraudx.online |
| **API docs (Swagger)** | `http://localhost:8000/docs` (when backend is running) |

T
---

## Tech stack

| Layer | Stack |
|-------|--------|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS, Sigma.js, Graphology, D3, react-force-graph-3d |
| **Backend** | FastAPI, Python 3.x, Pandas, NetworkX, Pydantic |
| **APIs** | REST; `POST /api/analyze` (CSV upload), `GET /api/results` (session token) |

---

## Prerequisites

- **Node.js** 18+ and **npm** (for frontend)
- **Python** 3.10+ and **pip** (for backend)

---

## Project structure

```
FraudX/
├── README.md                 # This file
├── frontend/                 # Next.js app
│   ├── app/
│   │   ├── check-fraud/      # Analysis page, graph, CSV parser
│   │   ├── client/           # API client, axios
│   │   ├── components/       # CSV upload, Loader, etc.
│   │   └── ...
│   ├── package.json
│   └── .env.example
└── backend/                  # FastAPI app
    ├── app/
    │   ├── api/              # analyze, results, health
    │   ├── engine/           # parser, pipeline, algorithms
    │   ├── config.py
    │   └── ...
    ├── requirements.txt
    └── .env
```

---

## Backend (FastAPI)

### Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Environment variables

Create a `.env` in `backend/` (see `backend/.env` for a full example). Key options:

| Variable | Description | Example |
|----------|-------------|---------|
| `FRONTEND_URL` | Allowed CORS origin | `http://localhost:3000` |
| `MAX_UPLOAD_SIZE_MB` | Max CSV size (MB) | `5` |
| `RESULT_STORE_TTL_SECONDS` | Session expiry | `3600` |
| `MIN_CYCLE_LENGTH` / `MAX_CYCLE_LENGTH` | Cycle detection | `3` / `5` |
| `SMURFING_WINDOW_HOURS` | Smurfing time window | `72` |
| `SUSPICIOUS_SCORE_THRESHOLD` | Min score to flag | `12.0` |

### Run

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API: **http://localhost:8000**
- Swagger UI: **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**

### API overview

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/analyze` | Upload CSV; returns `session_token` and full result (suspicious_accounts, fraud_rings, summary, graph) |
| `GET` | `/api/results` | Get stored result; header `X-Session-Token: <token>`; optional query params: `account_id`, `ring_id`, `min_score`, `pattern` |

---

## Frontend (Next.js)

### Setup

```bash
cd frontend
npm install
```

### Environment variables

Create `.env.local` in `frontend/` (optional):

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |

### Run

```bash
cd frontend
npm run dev
```

- App: **http://localhost:3000**
- Upload CSV on the home page → redirects to `/check-fraud?session=<token>`.

### Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start dev server |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |

---

## CSV format

The backend and frontend expect a CSV with these columns (names are case-insensitive, trimmed):

| Column | Description |
|--------|-------------|
| `transaction_id` | Unique transaction ID |
| `sender_id` | Sender account ID |
| `receiver_id` | Receiver account ID |
| `amount` | Transaction amount (numeric, > 0) |
| `timestamp` | Timestamp (parsed by backend) |

- Duplicate `transaction_id` rows are dropped (first kept).
- Self-loops (`sender_id == receiver_id`) are dropped.
- Frontend parses the same CSV to build the full node/edge graph; backend provides suspicion scores and fraud rings for coloring and rings.

---

## Running full stack

1. Start backend: `cd backend && uvicorn main:app --reload --port 8000`
2. Start frontend: `cd frontend && npm run dev`
3. Open **http://localhost:3000**, upload a CSV, then explore the graph and export JSON.

---

## Docs links

- **Backend API (OpenAPI)** — http://localhost:8000/docs  
- **Frontend** — Next.js [App Router docs](https://nextjs.org/docs/app)

---


