import React from "react";
import Dashboard from "./pages/Dashboard";

export default function App() {
  return (
    <div className="app-shell">
      <div className="app-header">
        <div>
          <span className="app-eyebrow">Clinical Decision-Support Prototype</span>
          <h1>Knee OA &amp; Implant Sizing — Analysis Viewbox</h1>
        </div>
      </div>
      <div className="disclaimer-banner">
        This is a clinical decision-support / research prototype. It does not diagnose
        osteoarthritis and does not replace review by a qualified orthopedic clinician.
        Segmentation currently runs in demo/mock mode unless a trained model has been connected
        (see backend/services/segmentation.py).
      </div>
      <Dashboard />
    </div>
  );
}