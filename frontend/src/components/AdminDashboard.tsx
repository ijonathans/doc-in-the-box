import { useEffect, useState } from "react";
import { loadAdminAppointments, loadAdminMetrics } from "../api";

type Metrics = {
  patients: number;
  appointments_total: number;
  appointments_booked: number;
};

type Appointment = {
  id: number;
  patient_id: number;
  doctor_name: string;
  status: string;
  appointment_time: string;
  insurance_verified: string;
};

export function AdminDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  useEffect(() => {
    async function load() {
      const loadedMetrics = await loadAdminMetrics();
      const loadedAppointments = await loadAdminAppointments();
      setMetrics(loadedMetrics);
      setAppointments(loadedAppointments);
    }
    load();
  }, []);

  return (
    <section className="panel">
      <h2>Admin Dashboard</h2>
      <p>
        Patients: {metrics?.patients ?? 0} | Appointments: {metrics?.appointments_total ?? 0} |
        Booked: {metrics?.appointments_booked ?? 0}
      </p>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Patient</th>
            <th>Doctor</th>
            <th>Status</th>
            <th>Time</th>
            <th>Insurance</th>
          </tr>
        </thead>
        <tbody>
          {appointments.map((item) => (
            <tr key={item.id}>
              <td>{item.id}</td>
              <td>{item.patient_id}</td>
              <td>{item.doctor_name}</td>
              <td>{item.status}</td>
              <td>{item.appointment_time}</td>
              <td>{item.insurance_verified}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

