import React, { useState } from "react";

/**
 * Wraps a set of named result panels in a tab switcher, so the six
 * result modules (Meniscus, Bones, Implant, OA comparison, Report,
 * optional Demographic estimate) can be reviewed quickly by clicking
 * rather than scrolling through a long stack — useful for live demos.
 */
export default function ResultsTabs({ tabs }) {
  const [active, setActive] = useState(0);

  return (
    <div>
      <div className="tabs" role="tablist" aria-label="Result sections">
        {tabs.map((t, i) => (
          <button
            key={t.label}
            role="tab"
            aria-selected={active === i}
            className={`tab-btn ${active === i ? "active" : ""}`}
            onClick={() => setActive(i)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div role="tabpanel">{tabs[active].content}</div>
    </div>
  );
}