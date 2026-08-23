import React, { useEffect, useRef, useState } from "react";

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
  const [sweepKey, setSweepKey] = useState(0);

  useEffect(() => {
    draw();
    setSweepKey((k) => k + 1); // re-trigger the scan-line sweep on new image/analysis
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

    // Femur region (top half) - phosphor cyan
    ctx.fillStyle = "rgba(79, 209, 197, 0.18)";
    ctx.fillRect(0, 0, w, midline);
    ctx.strokeStyle = "rgba(79, 209, 197, 0.85)";
    ctx.strokeRect(0, 0, w, midline);

    // Tibia region (bottom half) - contrast amber
    ctx.fillStyle = "rgba(232, 163, 61, 0.18)";
    ctx.fillRect(0, midline, w, h - midline);
    ctx.strokeStyle = "rgba(232, 163, 61, 0.85)";
    ctx.strokeRect(0, midline, w, h - midline);

    // Meniscus band (medial half, around midline) - bone white
    const bandHalf = Math.max(2, h / 60);
    ctx.fillStyle = "rgba(237, 239, 242, 0.28)";
    ctx.fillRect(0, midline - bandHalf, w / 2, bandHalf * 2);
    ctx.strokeStyle = "rgba(237, 239, 242, 0.9)";
    ctx.strokeRect(0, midline - bandHalf, w / 2, bandHalf * 2);

    // Sampling location markers (anterior / mid / posterior) - signal red
    const locations = analysis?.meniscus?.locations_px || {};
    const fractions = { anterior: 0.2, mid: 0.5, posterior: 0.8 };
    Object.entries(fractions).forEach(([label, frac]) => {
      if (locations[label] === null || locations[label] === undefined) return;
      const x = frac * (w / 2);
      ctx.beginPath();
      ctx.arc(x, midline, 5, 0, Math.PI * 2);
      ctx.fillStyle = "#FF6B6B";
      ctx.fill();
      ctx.fillStyle = "#FF6B6B";
      ctx.font = "600 12px 'JetBrains Mono', monospace";
      ctx.fillText(label, x - 14, midline - bandHalf - 8);
    });
  }

  return (
    <div className="panel">
      <h2>3. Knee Image & Segmentation Overlay</h2>
      <div className="image-canvas-wrap viewbox">
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
            <div className="scan-sweep" key={sweepKey} aria-hidden="true" />
          </>
        ) : (
          <span style={{ color: "#4A5866", fontFamily: "var(--font-mono)", fontSize: 13 }}>
            No image loaded — upload a knee image to preview it here.
          </span>
        )}
      </div>
      <div className="legend">
        <span><span className="legend-swatch" style={{ background: "#4FD1C5" }}></span>Femur (mock region)</span>
        <span><span className="legend-swatch" style={{ background: "#E8A33D" }}></span>Tibia (mock region)</span>
        <span><span className="legend-swatch" style={{ background: "#EDEFF2" }}></span>Meniscus band</span>
        <span><span className="legend-swatch" style={{ background: "#FF6B6B" }}></span>Sample point</span>
      </div>
      {analysis && (
        <div className="small-note">
          Segmentation mode: <strong>{analysis.mode}</strong> — {analysis.segmentation_disclaimer}
        </div>
      )}
    </div>
  );
}