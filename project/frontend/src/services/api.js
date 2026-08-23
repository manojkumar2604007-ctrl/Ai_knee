const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

async function handle(response) {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

export async function createPatient(patient) {
  const res = await fetch(`${API_BASE}/patient`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patient),
  });
  return handle(res);
}

export async function getPatient(patientId) {
  const res = await fetch(`${API_BASE}/patient/${patientId}`);
  return handle(res);
}

export async function uploadImage(patientId, file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/upload?patient_id=${patientId}`, {
    method: "POST",
    body: formData,
  });
  return handle(res);
}

export async function analyzeImage(patientId, imageId, manualMmPerPixel) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      patient_id: patientId,
      image_id: imageId,
      manual_mm_per_pixel: manualMmPerPixel || null,
    }),
  });
  return handle(res);
}

export async function getMeasurements(patientId) {
  const res = await fetch(`${API_BASE}/measurements/${patientId}`);
  return handle(res);
}

export async function getImplantRecommendation(patientId) {
  const res = await fetch(`${API_BASE}/implant-recommendation/${patientId}`);
  return handle(res);
}

export async function getOaComparison() {
  const res = await fetch(`${API_BASE}/oa-comparison`);
  return handle(res);
}

export async function listImplants() {
  const res = await fetch(`${API_BASE}/implant-database`);
  return handle(res);
}

export async function addImplant(implant) {
  const res = await fetch(`${API_BASE}/implant-database`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(implant),
  });
  return handle(res);
}

export async function getDemographicEstimate(patientId) {
  const res = await fetch(`${API_BASE}/demographic-estimate/${patientId}`);
  return handle(res);
}

export const API_BASE_URL = API_BASE;