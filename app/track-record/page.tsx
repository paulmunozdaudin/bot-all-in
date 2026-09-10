import { apiGet } from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";

interface TrackRecordSummary {
  total_predictions: number;
  resolved_predictions: number;
  correct_predictions: number;
  brier_score: number | null;
  log_loss: number | null;
  clv: number | null;
  reason: string;
}

export default async function TrackRecordPage() {
  let summary: TrackRecordSummary | null = null;
  let fetchError: string | null = null;

  try {
    summary = await apiGet<TrackRecordSummary>("/track-record/summary");
  } catch {
    fetchError = "Could not reach the Football AI API. Is the backend running?";
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Model Track Record</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Every prediction below was logged before kickoff and has never been edited.
          Negative results are shown, not hidden.
        </p>
      </header>

      {fetchError ? (
        <EmptyState title="API unavailable" reason={fetchError} />
      ) : summary && summary.total_predictions === 0 ? (
        <EmptyState title="No track record yet" reason={summary.reason} />
      ) : summary ? (
        <div className="grid gap-4 sm:grid-cols-3">
          <Stat label="Total predictions" value={summary.total_predictions} />
          <Stat label="Resolved" value={summary.resolved_predictions} />
          <Stat label="Correct" value={summary.correct_predictions} />
          <Stat label="Brier Score" value={summary.brier_score ?? "-"} />
          <Stat label="Log Loss" value={summary.log_loss ?? "-"} />
          <Stat label="CLV" value={summary.clv ?? "-"} />
        </div>
      ) : null}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border border-neutral-800 p-4">
      <p className="text-xs text-neutral-500">{label}</p>
      <p className="mt-1 text-xl font-semibold">{value}</p>
    </div>
  );
}
