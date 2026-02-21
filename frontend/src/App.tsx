import { useState } from "react";
import { AdminDashboard } from "./components/AdminDashboard";
import { PatientIntake } from "./components/PatientIntake";

export default function App() {
  const [tab, setTab] = useState<"patient" | "admin">("patient");

  return (
    <main className="container">
      <h1>Hacklytics GenAI Healthcare Agent</h1>
      <div className="tabs">
        <button onClick={() => setTab("patient")}>Patient View</button>
        <button onClick={() => setTab("admin")}>Admin View</button>
      </div>
      {tab === "patient" ? <PatientIntake /> : <AdminDashboard />}
    </main>
  );
}

