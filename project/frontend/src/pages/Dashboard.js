import React, { useState } from "react";
import PatientForm from "../components/PatientForm";
import ImageUpload from "../components/ImageUpload";
import ImageViewer from "../components/ImageViewer";
import MeniscusResults from "../components/MeniscusResults";
import OAComparison from "../components/OAComparison";
import BoneMeasurements from "../components/BoneMeasurements";
import ImplantMatching from "../components/ImplantMatching";
import FinalReport from "../components/FinalReport";
import DemographicEstimate from "../components/demographic_estimate";

export default function Dashboard() {
  const [patient, setPatient] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState(null);
  const [oaRefreshKey, setOaRefreshKey] = useState(0);

  function handleImageSelected(file) {
    setImagePreviewUrl(URL.createObjectURL(file));
  }

  function handleAnalysisComplete(result) {
    setAnalysis(result);
    setOaRefreshKey((k) => k + 1); // refresh population comparison
  }

  return (
    <div className="grid">
      <div>
        <PatientForm onPatientCreated={setPatient} patient={patient} />
        <ImageUpload
          patient={patient}
          onImageSelected={handleImageSelected}
          onAnalysisComplete={handleAnalysisComplete}
        />
      </div>

      <div>
        <ImageViewer imageUrl={imagePreviewUrl} analysis={analysis} />
        <div className="two-col">
          <MeniscusResults analysis={analysis} />
          <BoneMeasurements analysis={analysis} />
        </div>
        <ImplantMatching analysis={analysis} />
        <OAComparison refreshKey={oaRefreshKey} />
        <FinalReport patient={patient} analysis={analysis} />

        <hr style={{ margin: "24px 0", border: "none", borderTop: "1px dashed var(--color-border)" }} />
        <DemographicEstimate patient={patient} analysis={analysis} />
      </div>
    </div>
  );
}