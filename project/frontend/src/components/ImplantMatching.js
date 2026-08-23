import React from "react";

function RecommendationTable({ title, rows }) {
  return (
    <div>
      <strong>{title}</strong>
      {rows && rows.length > 0 ? (
        <table className="measurement-table">
          <thead>
            <tr><th>Size</th><th>System</th><th>Match score</th></tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td>{r.size}</td>
                <td>{r.implant_system}</td>
                <td>{r.match_score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="small-note">No candidates matched (uncalibrated measurement or empty database).</p>
      )}
    </div>
  );
}

export default function ImplantMatching({ analysis }) {
  if (!analysis) {
    return (
      <div className="panel">
        <h2>8. Implant-Size Matching</h2>
        <p className="small-note">Run an analysis to see ranked implant size candidates.</p>
      </div>
    );
  }

  const rec = analysis.implant_recommendation;

  return (
    <div className="panel">
      <h2>8. Implant-Size Matching</h2>
      <div className="two-col">
        <RecommendationTable title="Femoral component" rows={rec.femoral_recommendations} />
        <RecommendationTable title="Tibial component" rows={rec.tibial_recommendations} />
      </div>
      <p className="small-note"><em>{rec.disclaimer}</em> Implant database currently holds placeholder
      dimensions — replace via POST /implant-database with validated manufacturer specs.</p>
    </div>
  );
}