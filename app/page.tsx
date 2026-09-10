import { EmptyState } from "@/components/EmptyState";
import { apiGet } from "@/lib/api";

interface MatchSummary {
  id: number;
  home_team: string;
  away_team: string;
  probabilities: { home: number; draw: number; away: number };
  expected_goals: { home: number; away: number };
  confidence: number;
}

export default async function HomePage() {
  let matches: MatchSummary[] = [];
  let fetchError: string | null = null;

  try {
    matches = await apiGet<MatchSummary[]>("/matches/today");
  } catch {
    fetchError = "Could not reach the Football AI API. Is the backend running?";
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Today</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Model probabilities, not predictions of a certain outcome. See{" "}
          <span className="text-neutral-400">Track Record</span> for historical performance.
        </p>
      </header>

      {fetchError ? (
        <EmptyState title="API unavailable" reason={fetchError} />
      ) : matches.length === 0 ? (
        <EmptyState
          title="No matches to show"
          reason="No data has been ingested yet in this environment (Phase 2 of the roadmap). This is not a fabricated slate -- see ROADMAP.md."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {matches.map((m) => (
            <div key={m.id} className="rounded-lg border border-neutral-800 p-4">
              <p className="font-medium">
                {m.home_team} vs {m.away_team}
              </p>
              <p className="mt-2 text-sm text-neutral-400">
                Home {(m.probabilities.home * 100).toFixed(0)}% · Draw{" "}
                {(m.probabilities.draw * 100).toFixed(0)}% · Away{" "}
                {(m.probabilities.away * 100).toFixed(0)}%
              </p>
              <p className="text-xs text-neutral-600">Model confidence: {m.confidence}/100</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
