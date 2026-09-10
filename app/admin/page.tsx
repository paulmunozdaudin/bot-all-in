import { apiGet } from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";

interface AdminStatus {
  checked_at: string;
  data_sources: Record<string, string>;
  model_version: string;
  last_backtest_run: string | null;
  last_ingestion_run: string | null;
}

export default async function AdminPage() {
  let status: AdminStatus | null = null;
  let fetchError: string | null = null;

  try {
    status = await apiGet<AdminStatus>("/admin/status");
  } catch {
    fetchError = "Could not reach the Football AI API. Is the backend running?";
  }

  if (fetchError || !status) {
    return <EmptyState title="API unavailable" reason={fetchError ?? "Unknown error."} />;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Admin</h1>
      <div className="rounded-lg border border-neutral-800 p-4 text-sm">
        <p className="text-neutral-500">Model version</p>
        <p className="mb-4">{status.model_version}</p>
        <p className="text-neutral-500">Data sources</p>
        <ul className="mb-4 list-inside list-disc">
          {Object.entries(status.data_sources).map(([source, state]) => (
            <li key={source}>
              {source}: <span className="text-neutral-400">{state}</span>
            </li>
          ))}
        </ul>
        <p className="text-neutral-500">Last backtest run</p>
        <p className="mb-4">{status.last_backtest_run ?? "never"}</p>
        <p className="text-neutral-500">Last ingestion run</p>
        <p>{status.last_ingestion_run ?? "never"}</p>
      </div>
    </div>
  );
}
