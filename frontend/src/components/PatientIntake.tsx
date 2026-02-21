import { FormEvent, useState } from "react";
import { registerPatient, runIntake } from "../api";

export function PatientIntake() {
  const [patientId, setPatientId] = useState<number | null>(null);
  const [symptoms, setSymptoms] = useState("");
  const [zipCode, setZipCode] = useState("10001");
  const [result, setResult] = useState<string>("");

  async function handleRegister(event: FormEvent) {
    event.preventDefault();
    const patient = await registerPatient({
      first_name: "Demo",
      last_name: "Patient",
      phone_number: "+15550001111",
      insurance_provider: "Aetna",
      insurance_member_id: "MEM-12345",
      chronic_conditions: "Hypertension"
    });
    setPatientId(patient.id);
  }

  async function handleIntake(event: FormEvent) {
    event.preventDefault();
    if (!patientId) return;
    const recommendation = await runIntake({
      patient_id: patientId,
      symptoms_text: symptoms,
      preferred_zip_code: zipCode
    });
    setResult(JSON.stringify(recommendation, null, 2));
  }

  return (
    <section className="panel">
      <h2>Patient Intake</h2>
      <p>Register patient then submit symptoms for AI recommendation.</p>
      <form onSubmit={handleRegister}>
        <button type="submit">Register Demo Patient</button>
      </form>
      <p>Patient Id: {patientId ?? "not registered"}</p>
      <form onSubmit={handleIntake}>
        <textarea
          value={symptoms}
          onChange={(event) => setSymptoms(event.target.value)}
          placeholder="Describe your symptoms..."
          required
        />
        <input value={zipCode} onChange={(event) => setZipCode(event.target.value)} required />
        <button type="submit" disabled={!patientId}>
          Run AI Intake
        </button>
      </form>
      <pre>{result}</pre>
    </section>
  );
}

