export const API_BASE = "/api";

export async function registerPatient(payload: {
  first_name: string;
  last_name: string;
  phone_number: string;
  insurance_provider: string;
  insurance_member_id: string;
  epic_patient_id?: string;
  chronic_conditions?: string;
}) {
  const response = await fetch(`${API_BASE}/patient/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error("Failed to register patient");
  return response.json();
}

export async function runIntake(payload: {
  patient_id: number;
  symptoms_text: string;
  preferred_zip_code: string;
}) {
  const response = await fetch(`${API_BASE}/patient/intake`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error("Failed to run intake");
  return response.json();
}

export async function loadAdminMetrics() {
  const response = await fetch(`${API_BASE}/admin/metrics`);
  if (!response.ok) throw new Error("Failed to load metrics");
  return response.json();
}

export async function loadAdminAppointments() {
  const response = await fetch(`${API_BASE}/admin/appointments`);
  if (!response.ok) throw new Error("Failed to load appointments");
  return response.json();
}

export type ChatApiResponse = {
  reply: string;
  session_id: string;
  state: Record<string, unknown>;
  needs_emergency: boolean;
  handoff_ready: boolean;
  outbound_call_started?: boolean;
  outbound_call_error?: string;
};

const CHAT_REQUEST_TIMEOUT_MS = 120_000;

export async function sendChatMessage(message: string, sessionId: string | null): Promise<ChatApiResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), CHAT_REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${API_BASE}/chat/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
      signal: controller.signal,
    });
    if (!response.ok) throw new Error("Failed to send chat message");
    return response.json();
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      throw new Error("Request took too long. The triage flow may be busy; please try again.");
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

export type PendingCallSummaryResponse = { summary: string | null };

export async function getPendingCallSummary(sessionId: string): Promise<PendingCallSummaryResponse> {
  const response = await fetch(
    `${API_BASE}/chat/pending-call-summary?session_id=${encodeURIComponent(sessionId)}`
  );
  if (!response.ok) throw new Error("Failed to get pending call summary");
  return response.json();
}

export async function consumeCallSummary(sessionId: string): Promise<{ ok: boolean }> {
  const response = await fetch(
    `${API_BASE}/chat/consume-call-summary?session_id=${encodeURIComponent(sessionId)}`,
    { method: "POST" }
  );
  if (!response.ok) throw new Error("Failed to consume call summary");
  return response.json();
}

