# ElevenLabs outbound call setup (clinics)

After the triage graph returns the top 3 clinics, the app can start an outbound call via ElevenLabs + Twilio to the first clinic to check availability and book an appointment. Calls are made **one by one**: if the first clinic books, the others are not called (handled via post-call webhook).

## What you need

1. **ElevenLabs account** – [elevenlabs.io](https://elevenlabs.io) (Conversational AI / Agents).
2. **Twilio account** – Already connected with ElevenLabs (you mentioned this is done).
3. **An ElevenLabs Conversational AI Agent** – You configure this in the ElevenLabs platform; the backend only starts the call and passes context (clinic name, chief complaint, etc.) and a system prompt override.

## Backend env vars (`.env`)

| Variable | Description |
|----------|-------------|
| `ELEVENLABS_API_KEY` | API key from ElevenLabs (Profile → API Key). |
| `ELEVENLABS_AGENT_ID` | The **Agent ID** of the agent you create for outbound clinic calls (from the agent's URL or settings). |
| `ELEVENLABS_AGENT_PHONE_NUMBER_ID` | The **Phone number ID** in ElevenLabs that represents your Twilio number (from ElevenLabs → Phone Numbers / Twilio integration). |

Twilio credentials (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`) are used by ElevenLabs when you connect Twilio in their dashboard; the backend does not call Twilio directly for outbound.

## Steps to set up

### 1. Create an agent in ElevenLabs

- In ElevenLabs, go to **Conversational AI** → **Agents** and create a new agent (or use an existing one).
- This agent will be used for **outbound** calls to clinic front desks. You can set a **default** system prompt in the UI; the backend **overrides** it per call with a prompt that:
  - Asks for availability and books an appointment only.
  - Uses dynamic variables: `clinic_name`, `clinic_address`, `chief_complaint`, and optionally `patient_first_name`.

Copy the **Agent ID** (e.g. from the agent's URL or API section) into `ELEVENLABS_AGENT_ID`.

### 2. Connect Twilio and get Phone number ID

- In ElevenLabs, connect your Twilio account (you said this is already done).
- Add or select the Twilio number that will **place** the outbound calls.
- In the ElevenLabs UI, find the **Phone number ID** for that number (often in the phone numbers / Twilio integration page). Put it in `ELEVENLABS_AGENT_PHONE_NUMBER_ID`.

### 3. Post-call webhook (required for Call_summarize)

- When a call ends, ElevenLabs sends a **post-call webhook** to your backend. The backend stores the transcript summary and links it to the chat session so the **Call_summarize** node can show it in chat.
- **Webhook URL**: Configure in ElevenLabs (agent or workspace webhook settings) to:
  - `https://your-backend-host/webhooks/elevenlabs/post-call`
  - For local dev with a tunnel (e.g. ngrok): `https://your-ngrok-url/webhooks/elevenlabs/post-call`
- The backend expects a JSON body with `conversation_id` and either an analysis summary or transcript (see [ElevenLabs post-call webhook docs](https://elevenlabs.io/docs/conversational-ai/workflows/post-call-webhooks)). When the user sends their next message (or the frontend polls), the graph runs the **Call_summarize** node first; if a pending summary exists for that session, it is returned as the chat reply and the node is the only one run for that turn.
- Optionally, your webhook handler can also start the next clinic call if the current one did not book (same `POST /v1/convai/twilio/outbound-call` with the next clinic).

## ngrok setup (connect ElevenLabs to local backend)

To receive the ElevenLabs post-call webhook on your machine, expose the backend with ngrok so ElevenLabs can reach `POST /webhooks/elevenlabs/post-call`.

1. **Install ngrok**  
   - Download from [ngrok.com](https://ngrok.com/download) or install via package manager (e.g. `winget install ngrok` or `choco install ngrok` on Windows).  
   - Sign up at [ngrok.com](https://ngrok.com) and run `ngrok config add-authtoken <your-token>` once.

2. **Start the backend**  
   From the `backend` folder (with your venv active):
   ```powershell
   uvicorn app.main:app --reload
   ```
   The API must be running on **port 8000** (uvicorn default).

3. **Start ngrok**  
   In a **second** terminal, run:
   ```powershell
   ngrok http 8000
   ```
   Or use the project script from the repo root:
   ```powershell
   .\backend\scripts\run_ngrok.ps1
   ```
   ngrok will print a public URL like `https://abc123.ngrok-free.app`.

4. **Configure ElevenLabs webhook**  
   - In the ElevenLabs dashboard (agent or workspace settings), set the **post-call webhook URL** to:
     `https://<your-ngrok-host>/webhooks/elevenlabs/post-call`  
     Example: `https://abc123.ngrok-free.app/webhooks/elevenlabs/post-call`  
   - Replace `<your-ngrok-host>` with the host from the ngrok terminal (the URL changes each time you restart ngrok unless you use a reserved domain).

5. **Keep both running**  
   Leave both the backend and ngrok running while testing. If you restart ngrok, the URL may change; update the webhook URL in ElevenLabs if needed.

## System prompt used per call

The backend sends this as the **prompt override** when starting each outbound call (see `app/graphs/outbound_call_node.py` → `OUTBOUND_CALL_AGENT_SYSTEM_PROMPT`). The agent will:

- Introduce that it's calling to schedule an appointment for a patient.
- Ask for next available time and book **only** (no medical advice).
- Use `clinic_name`, `clinic_address`, `chief_complaint` from the triage context.

You can change this text in the code or later support overriding it via config.

## Flow summary

1. User completes triage and consents to booking → RAG + provider locations → **top 3 clinics** in state.
2. **Provider locations node** runs → **Outbound call node** runs.
3. Outbound call node starts **one** Twilio outbound call to the first clinic (index 0) with the system prompt and dynamic variables.
4. When the call ends, ElevenLabs sends a POST to **/webhooks/elevenlabs/post-call**. The backend stores the transcript summary for that session.
5. When the user sends their next message, the graph runs **Call_summarize** first. If a pending summary exists, it is shown as the chat reply ("**Call summary**" plus the transcript summary); otherwise the graph continues to the router as usual.

Without a post-call webhook configured in ElevenLabs, the Call_summarize node will never have a pending summary to show; configure the webhook URL so the backend can receive the call result and transcript.

## Testing the calling workflow

To test the full flow (outbound call then summarization in chat):

**Prerequisites**

- `.env` has `ELEVENLABS_API_KEY`, `ELEVENLABS_AGENT_ID`, and `ELEVENLABS_AGENT_PHONE_NUMBER_ID` set.
- Redis running (session store and pending call summary).
- Backend on port 8000; ngrok tunnel to 8000; ElevenLabs post-call webhook set to `https://<ngrok-host>/webhooks/elevenlabs/post-call`.

**Manual test steps**

1. Start backend: `uvicorn app.main:app --reload` from `backend`.
2. Start ngrok: `ngrok http 8000` (or `.\backend\scripts\run_ngrok.ps1`).
3. In ElevenLabs, set post-call webhook URL to `https://<ngrok-host>/webhooks/elevenlabs/post-call`.
4. Via the app (or chat API), run a conversation until the graph reaches **ask_booking_consent** then **provider_locations** then **outbound_call_node** (so a call is started using the agent from .env).
5. Complete or end the call on the phone side.
6. Wait for ElevenLabs to send the post-call webhook (backend stores the summary in Redis keyed by session).
7. Send any follow-up message in the same session; the graph runs **call_summarize_node** first, finds the pending summary, and returns it as `assistant_reply` (e.g. "**Call summary** …") and routes to END.

**Receive a single test call**

To trigger one outbound call to your phone without going through the full triage flow, set `OUTBOUND_CALL_TEST_PHONE` in `.env` (E.164, e.g. `+15551234567`) and run:

```powershell
cd backend
pytest tests/test_outbound_call.py -v -m integration
```

Your phone will ring; the test asserts that the ElevenLabs API reported success.

## No call received?

1. **Check the chat reply** – After the flow runs, the reply will say either:
   - "We're calling [Clinic] now at [phone]..." → the API accepted the request; if you still get no call, see 4–5 below.
   - "We couldn't start the call... Error: ..." → the backend could not start the call; the error message and `outbound_call_error` in the API response tell you why.

2. **All three env vars must be set** – In `.env`: `ELEVENLABS_API_KEY`, `ELEVENLABS_AGENT_ID`, `ELEVENLABS_AGENT_PHONE_NUMBER_ID`. Restart the backend after changing `.env`.

3. **Flow must reach the outbound step** – You must complete triage (chief complaint + timeline), say yes to booking, then get the "Here are 3 clinics" message. The outbound call is triggered only on the **next** step after that (when the graph runs provider_locations then outbound_call_node).

4. **Phone number ID** – `ELEVENLABS_AGENT_PHONE_NUMBER_ID` is the ID of your Twilio number **inside ElevenLabs** (Phone Numbers / Twilio integration), not the Twilio number itself. Copy it from the ElevenLabs dashboard.

5. **Twilio / number** – In ElevenLabs, the connected Twilio number must be able to place outbound calls. In Twilio, check that the number is active and that outbound calls are allowed (no geo or carrier blocks for your test numbers).
