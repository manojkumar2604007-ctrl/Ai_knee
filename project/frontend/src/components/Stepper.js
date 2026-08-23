import React from "react";

/**
 * Horizontal progress stepper reflecting the ACTUAL pipeline sequence
 * a user moves through: create a patient, upload an image, run the
 * analysis, then review results. Each step's state (done/active/upcoming)
 * is derived from real app state in Dashboard.js, not decorative.
 */
export default function Stepper({ steps, activeIndex }) {
  return (
    <div className="stepper" role="list" aria-label="Analysis pipeline progress">
      {steps.map((label, i) => (
        <React.Fragment key={label}>
          <div
            className={`stepper-step ${i === activeIndex ? "active" : ""} ${i < activeIndex ? "done" : ""}`}
            role="listitem"
          >
            <span className="stepper-dot">{i < activeIndex ? "✓" : i + 1}</span>
            <span className="stepper-label">{label}</span>
          </div>
          {i < steps.length - 1 && <span className="stepper-connector" aria-hidden="true" />}
        </React.Fragment>
      ))}
    </div>
  );
}