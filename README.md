# Hacklytics GenAI Healthcare Agent

A proactive patient-facing AI agent that:

- Gathers patient symptom details via chat (triage flow),
- Uses Epic FHIR history when configured,
- Searches ZocDoc for doctor availability and insurance fit,
- Calls medical offices via ElevenLabs to verify in-network coverage and book slots,
- Sends appointment confirmations via SMS (Twilio),
- Stores long-term patient memory using Actian VectorAI DB with PostgreSQL.

## For teammates: getting started

**Use the [STARTUP_GUIDE.md](STARTUP_GUIDE.md)** for full setup: prerequisites, PostgreSQL/Actian/Redis, backend `.env`, how to run backend and frontend, and ngrok for ElevenLabs webhooks.

**TL;DR:** From repo root: run PostgreSQL (+ Redis recommended). In `backend`: copy `.env.example` to `.env`, create venv, `pip install -r requirements.txt`, `uvicorn app.main:app --reload`. In `frontend`: `npm install`, `npm run dev`. Open **http://localhost:5173** for the app and **http://localhost:8000/docs** for the API.

**Accessing via ngrok:** If you serve the frontend through an ngrok URL (e.g. `https://xxx.ngrok-free.dev`), Vite may block the host. The project allows all hosts in `frontend/vite.config.ts` (`server.allowedHosts: true`). Restart `npm run dev` after pulling; the "Blocked request. This host is not allowed" error should go away.

## Project structure

- **backend** — FastAPI app, LangGraph triage/orchestration, ZocDoc/ElevenLabs/Twilio integrations, Actian memory, webhooks.
- **frontend** — React + TypeScript + Vite; patient chat UI and views (appointment, insurance, profile).

## Backend quick start

1. `cd backend`; create venv and activate it.
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set credentials (see STARTUP_GUIDE).
4. Run `uvicorn app.main:app --reload` → API at **http://localhost:8000**

## Frontend quick start

1. `cd frontend`; `npm install`
2. `npm run dev` → UI at **http://localhost:5173**

## Actian vector memory

1. Start Actian VectorAI DB (e.g. `localhost:50051`) per: https://github.com/hackmamba-io/actian-vectorAI-db-beta
2. Set in `backend/.env`: `ACTIAN_HOST`, `ACTIAN_COLLECTION_NAME`, `EMBEDDING_MODEL`, `MEMORY_TOP_K`, `MEMORY_VECTOR_DIMENSION`
3. The API persists profile/symptom/appointment memory to Actian and retrieves context for triage.

