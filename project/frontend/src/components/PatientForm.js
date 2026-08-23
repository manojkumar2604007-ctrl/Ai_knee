import React, { useState } from "react";
import { createPatient } from "../services/api";

export default function PatientForm({ onPatientCreated, patient }) {
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [sex, setSex] = useState("F");
  const [oaStatus, setOaStatus] = useState("Unknown");
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setStatus(null);
    try {
      const created = await createPatient({
        name: name || null,
        age: Number(age),
        sex,
        oa_status: oaStatus,
      });
      onPatientCreated(created);
      setStatus({ type: "success", msg: `Patient #${created.id} created.` });
    } catch (err) {
      setStatus({ type: "error", msg: err.message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <h2>1. Patient Information</h2>
      <form onSubmit={handleSubmit}>
        <label>Name (optional)</label>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Anonymized ID" />

        <label>Age</label>
        <input type="number" min="0" max="120" required value={age} onChange={(e) => setAge(e.target.value)} />

        <label>Sex</label>
        <select value={sex} onChange={(e) => setSex(e.target.value)}>
          <option value="F">Female</option>
          <option value="M">Male</option>
          <option value="Other">Other</option>
        </select>

        <label>Osteoarthritis Status (clinically labelled)</label>
        <select value={oaStatus} onChange={(e) => setOaStatus(e.target.value)}>
          <option value="Unknown">Unknown</option>
          <option value="OA">OA</option>
          <option value="Non-OA">Non-OA</option>
        </select>

        <button type="submit" disabled={loading}>
          {loading ? "Saving..." : patient ? "Update / Create New Patient" : "Create Patient"}
        </button>
      </form>
      {status && <div className={`status-msg ${status.type}`}>{status.msg}</div>}
      {patient && (
        <div className="small-note">
          Active patient: #{patient.id} — Age {patient.age}, {patient.sex}, {patient.oa_status}
        </div>
      )}
    </div>
  );
}