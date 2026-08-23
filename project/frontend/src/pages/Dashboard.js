import React, { useState } from "react";
import PatientForm from "../components/PatientForm";
import ImageUpload from "../components/ImageUpload";
import ImageViewer from "../components/ImageViewer";
import MeniscusResults from "../components/MeniscusResults";
import OAComparison from "../components/OAComparison";
import BoneMeasurements from "../components/BoneMeasurements";
import ImplantMatching from "../components/ImplantMatching";
import FinalReport from "../components/FinalReport";
import DemographicEstimate from "../components/DemographicEstimate";
import Stepper from "../components/Stepper";
import ResultsTabs from "../components/ResultsTabs";

const STEPS = ["Patient", "Upload", "Analyze", "Results"];

export default function Dashboard() {
  const [patient, setPatient] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState(null);
  const [imageSelected, setImageSelected] = useState(false);
  const [oaRefreshKey, setOaRefreshKey] = useState(0);

  function handleImageSelected(file) {
    setImagePreviewUrl(URL.createObjectURL(file));
    setImageSelected(true);
  }

  function handleAnalysisComplete(result) {
    setAnalysis(result);
    setOaRefreshKey((k) => k + 1); // refresh population comparison
  }

  // Derive the active pipeline step from real app state, not decoration.
  let activeIndex = 0;
  if (patient) activeIndex = 1;
  if (patient && imageSelected) activeIndex = 2;
  if (patient && imageSelected && analysis) activeIndex = 3;

  const resultTabs = [
    { label: "Meniscus", content: <MeniscusResults analysis={analysis} /> },
    { label: "Femur / Tibia", content: <BoneMeasurements analysis={analysis} /> },
    { label: "Implant Sizing", content: <ImplantMatching analysis={analysis} /> },
    { label: "OA Comparison", content: <OAComparison refreshKey={oaRefreshKey} /> },
    { label: "Final Report", content: <FinalReport patient={patient} analysis={analysis} /> },
    { label: "Sex / Maturity (optional)", content: <DemographicEstimate patient={patient} analysis={analysis} /> },
  ];

  return (
    <>
      <Stepper steps={STEPS} activeIndex={activeIndex} />
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
          <ResultsTabs tabs={resultTabs} />
        </div>
      </div>
    </>
  );
}