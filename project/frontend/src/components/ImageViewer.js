import React, { useEffect, useRef } from "react";

/**
 * Renders the uploaded knee image with an overlay indicating the
 * approximate femur / tibia / medial-meniscus regions and the
 * anterior/mid/posterior sampling locations used for thickness
 * measurement.
 *
 * NOTE: In "demo_mock" mode the backend segmentation is a simple
 * heuristic (top-half = femur, bottom-half = tibia, a thin medial
 * band = meniscus) rather than a real learned segmentation, so this
 * overlay is illustrative of *where* measurements were sampled, not a
 * pixel-accurate mask render. Once a trained model is wired in
 * (mode = "trained_model"), the backend can be extended to return
 * real mask PNGs/contours for a pixel-accurate overlay.
 */
export default function ImageViewer({ imageUrl, analysis }) {
  const canvasRef = useRef(null);
  const imgRef = useRef(null);

  useEffect(() => {
    draw();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [imageUrl, analysis]);

  function draw() {
    const canvas = canvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img || !img.complete || img.naturalWidth === 0) return;

    const w = img.naturalWidth;
    const h = img.naturalHeight;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, w, h);
    ctx.drawImage(img, 0, 0, w, h);

    if (!analysis) return;

    const midline = h / 2;

    // Femur region (top half) - blue
    ctx.fillStyle = "rgba(59, 130, 246, 0.25)";
    ctx.fillRect(0, 0, w, midline);
    ctx.strokeStyle = "rgba(59, 130, 246, 0.9)";
    ctx.strokeRect(0, 0, w, midline);

    // Tibia region (bottom half) - green
    ctx.fillStyle = "rgba(42, 157, 143, 0.25)";
    ctx.fillRect(0, midline, w, h - midline);
    ctx.strokeStyle = "rgba(42, 157, 143, 0.9)";
    ctx.strokeRect(0, midline, w, h - midline);

    // Meniscus band (medial half, around midline) - orange
    const bandHalf = Math.max(2, h / 60);
    ctx.fillStyle = "rgba(245, 158, 11, 0.35)";
    ctx.fillRect(0, midline - bandHalf, w / 2, bandHalf * 2);
    ctx.strokeStyle = "rgba(245, 158, 11, 0.9)";
    ctx.strokeRect(0, midline - bandHalf, w / 2, bandHalf * 2);

    // Sampling location markers (anterior / mid / posterior)
    const locations = analysis?.meniscus?.locations_px || {};
    const fractions = { anterior: 0.2, mid: 0.5, posterior: 0.8 };
    Object.entries(fractions).forEach(([label, frac]) => {
      if (locations[label] === null || locations[label] === undefined) return;
      const x = frac * (w / 2);
      ctx.beginPath();
      ctx.arc(x, midline, 5, 0, Math.PI * 2);
      ctx.fillStyle = "#b3261e";
      ctx.fill();
      ctx.fillStyle = "#b3261e";
      ctx.font = "12px sans-serif";
      ctx.fillText(label, x - 12, midline - bandHalf - 6);
    });
  }

  return (
    <div className="panel">
      <h2>3. Knee Image & Segmentation Overlay</h2>
      <div className="image-canvas-wrap">
        {imageUrl ? (
          <>
            <img
              ref={imgRef}
              src={imageUrl}
              alt="knee"
              style={{ display: "none" }}
              onLoad={draw}
              crossOrigin="anonymous"
            />
            <canvas ref={canvasRef} />
          </>
        ) : (
          <span style={{ color: "#9fb0b8" }}>Upload an image to preview it here.</span>
        )}
      </div>
      <div className="legend">
        <span><span className="legend-swatch" style={{ background: "#3b82f6" }}></span>Femur (mock region)</span>
        <span><span className="legend-swatch" style={{ background: "#2a9d8f" }}></span>Tibia (mock region)</span>
        <span><span className="legend-swatch" style={{ background: "#f59e0b" }}></span>Meniscus band</span>
        <span><span className="legend-swatch" style={{ background: "#b3261e" }}></span>Sample point</span>
      </div>
      {analysis && (
        <div className="small-note">
          Segmentation mode: <strong>{analysis.mode}</strong> — {analysis.segmentation_disclaimer}
        </div>
      )}
    </div>
  );
}