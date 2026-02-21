# Hacklytics GenAI Healthcare Agent

This project contains a proactive patient-facing AI agent that:

- gathers patient symptom details,
- uses Epic FHIR history context,
- searches ZocDoc doctor availability and insurance fit,
- calls medical offices via ElevenLabs to verify in-network coverage and slots,
- sends appointment confirmations via SMS.
- stores long-term patient memory using Actian VectorAI DB with PostgreSQL as structured storage.

## Project Structure

- `backend` - FastAPI app, orchestration services, data models, and background jobs.
- `frontend` - React TypeScript app for patient and admin views.

## Backend Quick Start

1. Create virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `backend/.env.example` to `backend/.env` and set credentials.
4. Run API with `uvicorn app.main:app --reload`.

## Actian Vector Memory Setup

1. Start Actian VectorAI DB container (`localhost:50051`) using the project guide:
   - `docker compose up`
2. Keep PostgreSQL running for transactional records.
3. Set memory env vars in `backend/.env`:
   - `ACTIAN_HOST`
   - `ACTIAN_COLLECTION_NAME`
   - `EMBEDDING_MODEL`
   - `MEMORY_TOP_K`
   - `MEMORY_VECTOR_DIMENSION`
4. The API will:
   - persist profile/symptom/appointment memory entries to Actian,
   - retrieve top-k memory context before triage.

Reference: https://github.com/hackmamba-io/actian-vectorAI-db-beta

## Frontend Quick Start

1. Install dependencies with `npm install`.
2. Start app with `npm run dev`.

