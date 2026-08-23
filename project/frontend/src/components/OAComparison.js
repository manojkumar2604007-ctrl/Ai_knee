import React, { useEffect, useState } from "react";
import { getOaComparison } from "../services/api";

function GroupCard({ title, group }) {
  return (
    <div>
      <strong>{title}</strong>
      <table className="measurement-table">
        <tbody>
          <tr><td>n</td><td>{group.n}</td></tr>
          <tr><td>Mean (mm)</td><td>{group.mean_mm ?? "—"}</td></tr>
          <tr><td>Std dev (mm)</td><td>{group.std_mm ?? "—"}</td></tr>
        </tbody>
      </table>
    </div>
  );
}

export default function OAComparison({ refreshKey }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const result = await getOaComparison();
        if (!cancelled) setData(result);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [refreshKey]);

  return (
    <div className="panel">
      <h2>5. OA / Non-OA & Sex Comparison (Population-wide)</h2>
      {loading && <p className="small-note">Loading comparison...</p>}
      {error && <p className="status-msg error">{error}</p>}
      {data && (
        <>
          <div className="two-col">
            <GroupCard title="OA" group={data.oa_vs_non_oa.oa_group} />
            <GroupCard title="Non-OA" group={data.oa_vs_non_oa.non_oa_group} />
          </div>
          <p className="small-note">
            Welch's t-test p-value: {data.oa_vs_non_oa.statistical_test.p_value ?? "n/a"} —{" "}
            {data.oa_vs_non_oa.statistical_test.note}
          </p>

          <div className="two-col" style={{ marginTop: 14 }}>
            <GroupCard title="Male" group={data.male_vs_female.male_group} />
            <GroupCard title="Female" group={data.male_vs_female.female_group} />
          </div>
          <p className="small-note">
            Welch's t-test p-value: {data.male_vs_female.statistical_test.p_value ?? "n/a"} —{" "}
            {data.male_vs_female.statistical_test.note}
          </p>
          <p className="small-note"><em>{data.disclaimer}</em></p>
        </>
      )}
    </div>
  );
}