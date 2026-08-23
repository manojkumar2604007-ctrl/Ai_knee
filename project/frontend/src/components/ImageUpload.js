import React, { useState } from "react";
import { uploadImage, analyzeImage } from "../services/api";

export default function ImageUpload({ patient, onAnalysisComplete, onImageSelected }) {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [manualSpacing, setManualSpacing] = useState("");
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleFileChange(e) {
    const f = e.target.files[0];
    setFile(f);
    setUploadResult(null);
    setStatus(null);
    if (f) {
      setPreviewUrl(URL.createObjectURL(f));
      onImageSelected && onImageSelected(f);
    }
  }

  async function handleUpload() {
    if (!patient) {
      setStatus({ type: "error", msg: "Create a patient first." });
      return;
    }
    if (!file) {
      setStatus({ type: "error", msg: "Choose an image file first." });
      return;
    }
    setLoading(true);
    setStatus(null);
    try {
      const result = await uploadImage(patient.id, file);
      setUploadResult(result);
      setStatus({
        type: result.pixel_spacing_mm ? "success" : "error",
        msg: result.pixel_spacing_mm
          ? `Calibration found in metadata: ${result.pixel_spacing_mm.toFixed(4)} mm/pixel.`
          : result.message,
      });
    } catch (err) {
      setStatus({ type: "error", msg: err.message });
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyze() {
    if (!uploadResult) {
      setStatus({ type: "error", msg: "Upload an image first." });
      return;
    }
    setLoading(true);
    try {
      const manual = uploadResult.pixel_spacing_mm ? null : (manualSpacing ? Number(manualSpacing) : null);
      const result = await analyzeImage(patient.id, uploadResult.image_id, manual);
      onAnalysisComplete(result);
      setStatus({ type: "success", msg: "Analysis complete — see results panels." });
    } catch (err) {
      setStatus({ type: "error", msg: err.message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <h2>2. Image Upload</h2>
      <label>Knee image (PNG / JPG / DICOM)</label>
      <input type="file" accept=".png,.jpg,.jpeg,.dcm" onChange={handleFileChange} />

      {previewUrl && (
        <div className="image-canvas-wrap" style={{ marginTop: 10, minHeight: 160 }}>
          <img src={previewUrl} alt="preview" />
        </div>
      )}

      <button onClick={handleUpload} disabled={loading}>Upload</button>

      {uploadResult && !uploadResult.pixel_spacing_mm && (
        <>
          <label>Manual calibration (mm per pixel) — required, metadata unavailable</label>
          <input
            type="number"
            step="0.0001"
            value={manualSpacing}
            onChange={(e) => setManualSpacing(e.target.value)}
            placeholder="e.g. 0.25"
          />
        </>
      )}

      {uploadResult && (
        <button className="secondary" onClick={handleAnalyze} disabled={loading}>
          {loading ? "Analyzing..." : "Run Analysis"}
        </button>
      )}

      {status && <div className={`status-msg ${status.type}`}>{status.msg}</div>}
    </div>
  );
}