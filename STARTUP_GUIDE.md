# Hacklytics App Startup Guide

This guide explains how to run the full app locally, including:

- Backend API (FastAPI)
- Frontend (React + Vite)
- Structured database (PostgreSQL)
- Long-term memory store (Actian VectorAI DB)
- Optional queue (Redis)

---

## 1) Prerequisites

Install these first:

- Python 3.10+
- Node.js 18+
- Docker Desktop (with WSL2 enabled on Windows)
- PostgreSQL 15+ (local or container)
- Redis (optional for now, recommended)

Verify tools:

```powershell
python --version
node --version
npm --version
docker --version
```

---

## 2) Project Structure

From project root:

- `backend` → FastAPI app, integrations, memory services
- `frontend` → React UI
- `backend/.env.example` → environment template

---

## 3) Start Infrastructure Services

You need PostgreSQL and Actian running before starting the API.

### 3.1 PostgreSQL

Make sure PostgreSQL is running and accessible.

Default app connection:

`postgresql+psycopg://postgres:postgres@localhost:5432/hacklytics`

Create the database if needed:

```sql
CREATE DATABASE hacklytics;
```

### 3.2 Actian VectorAI DB

Use the official repository instructions:

https://github.com/hackmamba-io/actian-vectorAI-db-beta

Expected endpoint in this app:

`localhost:50051`

### 3.3 Redis (optional but recommended)

If you plan to use Celery/background tasks, run Redis on:

`localhost:6379`

---

## 4) Configure Backend Environment

Go to `backend` and copy env template:

```powershell
cd backend
Copy-Item .env.example .env
```

Edit `.env` and set values.

### Required for basic local run

- `DATABASE_URL`
- `ACTIAN_HOST`
- `ACTIAN_COLLECTION_NAME`
- `MEMORY_TOP_K`
- `MEMORY_VECTOR_DIMENSION`

### Required for real integrations (otherwise mocks/fallbacks run)

- `OPENAI_API_KEY`
- `ZOCDOC_CLIENT_ID`
- `ZOCDOC_CLIENT_SECRET`
- `EPIC_CLIENT_ID`
- `EPIC_CLIENT_SECRET`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_AGENT_ID`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`

---

## 5) Install Backend Dependencies

From `backend`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If `actiancortex` fails from pip index, install it using the wheel/process in the Actian repo.

---

## 6) Start Backend API

From `backend` (venv active):

```powershell
uvicorn app.main:app --reload
```

API runs at:

`http://localhost:8000`

Health check:

`GET http://localhost:8000/health`

---

## 7) Install and Start Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs at:

`http://localhost:5173`

---

## 8) Validate Main User Flow

Use Swagger UI:

`http://localhost:8000/docs`

Run this order:

1. `POST /patient/register`
2. `POST /patient/intake`
3. `POST /patient/appointments`
4. `GET /patient/{patient_id}/appointments`

Validate memory:

1. `GET /admin/memory/{patient_id}`
2. `POST /admin/memory/{patient_id}/reindex`

---

## 9) What Happens If Credentials Are Missing

Current app behavior includes safe local fallbacks:

- ZocDoc returns mock doctors
- Epic returns mock/no history
- ElevenLabs call verification is simulated
- Twilio SMS returns mock status
- OpenAI embeddings use deterministic fallback vectors

This allows local testing before full production credentials are ready.

---

## 10) Troubleshooting

### Backend starts but DB errors appear

- Check `DATABASE_URL`
- Confirm PostgreSQL is running
- Confirm `hacklytics` database exists

### Memory endpoints return empty

- Confirm Actian service is running on `ACTIAN_HOST`
- Confirm collection name in `.env` matches expected value
- Run intake/booking first so memory is written

### `pytest` command not found

- Ensure venv is activated
- Install deps from `requirements.txt`
- Verify interpreter is your venv python

### Frontend cannot reach API

- Ensure backend is running at `http://localhost:8000`
- Verify frontend API base URL in `frontend/src/api.ts`

---

## 11) Recommended Startup Order (Every Time)

1. PostgreSQL
2. Actian VectorAI DB
3. Redis (optional)
4. Backend (`uvicorn`)
5. Frontend (`npm run dev`)

