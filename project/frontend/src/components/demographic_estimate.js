import React, { useEffect, useState } from "react";
import { getDemographicEstimate } from "../services/api";

/**
 * OPTIONAL ADD-ON PANEL — not one of the two required modules.
 * Shown only after an analysis has run. Clearly labelled as an
 * experimental statistical estimate requiring clinician review; it
 * never feeds back into the OA/meniscus comparison or implant sizing.
 */
export default function DemographicEstimate({ patient, analysis }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!patient || !analysis) {
      setData(null);
      setError(null);
      return;
    }
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      setData(null); // clear any stale result from a previous patient/analysis immediately
      try {
        const result = await getDemographicEstimate(patient.id);
        if (!cancelled) setData(result);
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
          setData(null); // ensure no stale panel content lingers under the error
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [patient, analysis]);

  if (!patient || !analysis) {
    return (
      <div className="panel">
        <h2>Optional: Sex / Skeletal Maturity Estimate</h2>
        <p className="small-note">Run an analysis to see this optional experimental estimate.</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <h2>Optional: Sex / Skeletal Maturity Estimate</h2>
      <span className="badge mock">Experimental add-on — not a core module</span>

      {loading && <p className="small-note">Loading estimate...</p>}
      {error && (
        <p className="small-note">
          No estimate available yet — run <strong>Run Analysis</strong> for this patient first.
        </p>
      )}

      {data && (
        <>
          <div className="report-block" style={{ marginTop: 10 }}>
            <h3>Sex (statistical estimate)</h3>
            <p>{data.sex_estimate.estimate}</p>
            <p className="small-note">{data.sex_estimate.confidence_note}</p>
          </div>

          <div className="report-block">
            <h3>Skeletal Maturity</h3>
            <p>{data.skeletal_maturity_estimate.estimate}</p>
            <p className="small-note">{data.skeletal_maturity_estimate.confidence_note}</p>
          </div>

          <p className="status-msg error" style={{ marginTop: 10 }}>
            {data.sex_estimate.disclaimer}
          </p>
          <p className="small-note"><em>{data.module_note}</em></p>
        </>
      )}
    </div>
  );
}