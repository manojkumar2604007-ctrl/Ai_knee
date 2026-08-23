import React from "react";

function BoneTable({ title, data }) {
  const calibrated = data?.calibration_status === "calibrated";
  return (
    <div>
      <strong>{title}</strong>{" "}
      <span className={`badge ${calibrated ? "calibrated" : "uncalibrated"}`}>
        {calibrated ? "mm" : "uncalibrated"}
      </span>
      <table className="measurement-table">
        <tbody>
          <tr><td>Width (px)</td><td>{data?.width_px ?? "—"}</td></tr>
          <tr><td>Width (mm)</td><td>{data?.width_mm ?? "—"}</td></tr>
          <tr><td>AP (px)</td><td>{data?.ap_px ?? "—"}</td></tr>
          <tr><td>AP (mm)</td><td>{data?.ap_mm ?? "—"}</td></tr>
        </tbody>
      </table>
      {!calibrated && (
        <p className="status-msg error">Physical measurement unavailable — image calibration required.</p>
      )}
    </div>
  );
}

export default function BoneMeasurements({ analysis }) {
  if (!analysis) {
    return (
      <div className="panel">
        <h2>6 & 7. Femoral / Tibial Measurements</h2>
        <p className="small-note">Run an analysis to see femur and tibia dimensions.</p>
      </div>
    );
  }
  return (
    <div className="panel">
      <h2>6 & 7. Femoral / Tibial Measurements</h2>
      <div className="two-col">
        <BoneTable title="Femur" data={analysis.femur} />
        <BoneTable title="Tibia" data={analysis.tibia} />
      </div>
    </div>
  );
}