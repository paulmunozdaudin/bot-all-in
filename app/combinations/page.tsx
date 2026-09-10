"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";

interface CombinationSearchResult {
  result: string;
  reason: string;
}

export default function CombinationLabPage() {
  const [riskProfile, setRiskProfile] = useState("balanced");
  const [maxSelections, setMaxSelections] = useState(4);
  const [result, setResult] = useState<CombinationSearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch() {
    setLoading(true);
    setError(null);
    try {
      const today = new Date().toISOString().slice(0, 10);
      const res = await apiPost<CombinationSearchResult>("/combinations/search", {
        date_from: today,
        date_to: today,
        competitions: [],
        markets: [],
        max_selections: maxSelections,
        risk_profile: riskProfile,
      });
      setResult(res);
    } catch {
      setError("Could not reach the Football AI API. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Combination Lab</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Searches for statistically coherent combinations, accounting for correlation
          between same-match markets. If nothing clears the bar, that is reported
          explicitly -- combinations are never forced.
        </p>
      </header>

      <div className="flex flex-wrap gap-4 rounded-lg border border-neutral-800 p-4">
        <label className="flex flex-col gap-1 text-sm">
          Risk profile
          <select
            value={riskProfile}
            onChange={(e) => setRiskProfile(e.target.value)}
            className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1"
          >
            <option value="conservative">Conservative</option>
            <option value="balanced">Balanced</option>
            <option value="high_variance">High variance</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Max selections
          <input
            type="number"
            min={2}
            max={8}
            value={maxSelections}
            onChange={(e) => setMaxSelections(Number(e.target.value))}
            className="w-20 rounded border border-neutral-700 bg-neutral-900 px-2 py-1"
          />
        </label>
        <button
          onClick={runSearch}
          disabled={loading}
          className="self-end rounded bg-neutral-100 px-4 py-1.5 text-sm font-medium text-neutral-900 disabled:opacity-50"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {result && (
        <div className="rounded-lg border border-dashed border-neutral-700 bg-neutral-900/40 p-6">
          <p className="text-sm font-medium text-neutral-300">{result.result}</p>
          <p className="mt-2 text-sm text-neutral-500">{result.reason}</p>
        </div>
      )}
    </div>
  );
}
