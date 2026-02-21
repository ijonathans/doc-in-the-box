const API_BASE = "http://localhost:8000";

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

