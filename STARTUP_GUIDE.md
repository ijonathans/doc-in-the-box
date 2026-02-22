# Doc-in-the-box Startup Guide

This guide helps teammates run the full app locally and understand how the pieces fit together.

**What this app does:** A patient-facing healthcare agent that collects symptoms via chat (triage), searches for providers (ZocDoc), calls clinics via ElevenLabs to book appointments, and stores long-term memory (Actian + PostgreSQL). The frontend is a React chat UI; the backend is a FastAPI + LangGraph orchestration layer.

**What you need to run:**
- Backend API (FastAPI) — chat, triage, outbound calls, webhooks
- Frontend (React + Vite) — patient chat UI
- PostgreSQL — transactional data (patients, appointments)
- Actian VectorAI DB — vector memory (optional for basic chat)
- Redis — session store and call-summary bridge (needed for multi-turn chat and ElevenLabs webhooks)

---

**Quick start (once env is set):** Backend: `cd backend` → activate venv → `uvicorn app.main:app --reload`. Frontend: `cd frontend` → `npm install` → `npm run dev`. Open `http://localhost:5173`.

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
- Verify frontend API base URL in `frontend/src/api.ts` (default is `http://localhost:8000`)

### "Blocked request. This host is not allowed" when using ngrok

- The frontend is served by Vite. When you open it via an ngrok URL (e.g. `https://xxx.ngrok-free.dev`), Vite blocks the request unless the host is allowed.
- **Fix:** The project already has `server.allowedHosts: true` in `frontend/vite.config.ts`, so all hosts (including any ngrok URL) are allowed. Restart the frontend dev server (`npm run dev`) after pulling. If you still see the error, confirm `vite.config.ts` contains `allowedHosts: true` under `server`.

---

## 11) Using ngrok (single tunnel)

**Why:** ElevenLabs sends post-call webhooks to your backend. In development, your machine is not publicly reachable. The app uses a **Vite proxy**: the frontend calls `/api/*`, and Vite forwards those requests to the backend (port 8000). So you need only **one** ngrok tunnel on port 5173.

**Single tunnel (recommended):**
1. Run backend: `uvicorn app.main:app --reload` (port 8000).
2. Run frontend: `npm run dev` (port 5173).
3. Run **one** tunnel: `ngrok http 5173`.
4. **Demo URL:** Use the ngrok HTTPS URL (e.g. `https://abc123.ngrok-free.app`) for the UI. The browser will request `/api/chat/message`, etc.; Vite proxies those to the backend.
5. **ElevenLabs webhook URL:** Set in ElevenLabs to `https://<your-ngrok-host>/api/webhooks/elevenlabs/post-call` (e.g. `https://abc123.ngrok-free.app/api/webhooks/elevenlabs/post-call`). Requests to that URL hit Vite on 5173, and Vite forwards to `http://localhost:8000/webhooks/elevenlabs/post-call`.

One public domain; frontend and backend appear unified; no CORS issues; no second tunnel.

---

## 12) Recommended Startup Order (Every Time)

1. Start PostgreSQL (ensure `hacklytics` DB exists).
2. Start Actian VectorAI DB (if using memory); see project link in §3.2.
3. Start Redis (required for chat sessions and ElevenLabs webhook call-summary flow).
4. From `backend` (with venv activated): `uvicorn app.main:app --reload` → API at `http://localhost:8000`.
5. From `frontend`: `npm install` (once), then `npm run dev` → UI at `http://localhost:5173`.

Optional: run `ngrok http 5173` and use that URL for the demo and for ElevenLabs webhook: `https://<ngrok-host>/api/webhooks/elevenlabs/post-call`.

