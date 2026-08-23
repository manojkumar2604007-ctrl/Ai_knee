import React from "react";

export default function MeniscusResults({ analysis }) {
  if (!analysis) {
    return (
      <div className="panel">
        <h2>4. Medial Meniscus Measurements</h2>
        <p className="small-note">Run an analysis to see meniscus thickness results.</p>
      </div>
    );
  }

  const { meniscus, calibration_status } = analysis;
  const calibrated = calibration_status === "calibrated";

  return (
    <div className="panel">
      <h2>4. Medial Meniscus Measurements</h2>
      <span className={`badge ${calibrated ? "calibrated" : "uncalibrated"}`}>
        {calibrated ? "Calibrated (mm)" : "Uncalibrated"}
      </span>

      {!calibrated && (
        <p className="status-msg error">
          Physical measurement unavailable — image calibration required.
        </p>
      )}

      <table className="measurement-table">
        <thead>
          <tr>
            <th>Location</th>
            <th>Thickness (px)</th>
            <th>Thickness (mm)</th>
          </tr>
        </thead>
        <tbody>
          {["anterior", "mid", "posterior"].map((loc) => (
            <tr key={loc}>
              <td style={{ textTransform: "capitalize" }}>{loc}</td>
              <td>{meniscus.locations_px?.[loc] ?? "—"}</td>
              <td>{meniscus.locations_mm?.[loc] ?? "—"}</td>
            </tr>
          ))}
          <tr>
            <td><strong>Mean</strong></td>
            <td>—</td>
            <td><strong>{meniscus.mean_mm ?? "—"}</strong></td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}