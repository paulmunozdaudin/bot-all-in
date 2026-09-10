import { EmptyState } from "@/components/EmptyState";
import { apiGet } from "@/lib/api";

interface OpportunitiesResponse {
  opportunities: unknown[];
  reason: string;
}

export default async function OpportunitiesPage() {
  let data: OpportunitiesResponse | null = null;
  let fetchError: string | null = null;

  try {
    data = await apiGet<OpportunitiesResponse>("/opportunities");
  } catch {
    fetchError = "Could not reach the Football AI API. Is the backend running?";
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Market Scanner</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Matches/markets where model probability exceeds normalized market-implied
          probability, after the Market Edge Engine&apos;s quality and stability gates.
          No sample size below the validated minimum is ever shown as a signal.
        </p>
      </header>

      {fetchError ? (
        <EmptyState title="API unavailable" reason={fetchError} />
      ) : !data || data.opportunities.length === 0 ? (
        <EmptyState
          title="No opportunities found"
          reason={data?.reason ?? "No qualifying signal found for the current filters."}
        />
      ) : (
        <pre className="overflow-x-auto rounded-lg border border-neutral-800 p-4 text-xs">
          {JSON.stringify(data.opportunities, null, 2)}
        </pre>
      )}
    </div>
  );
}
