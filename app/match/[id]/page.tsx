import { EmptyState } from "@/components/EmptyState";
import { apiGet } from "@/lib/api";

export default async function MatchPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let reason = "Unknown error.";
  try {
    const data = await apiGet<{ status: string; reason: string }>(`/matches/${id}`);
    reason = data.reason;
  } catch {
    reason = "Could not reach the Football AI API. Is the backend running?";
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Match #{id}</h1>
      <EmptyState title="No data for this match" reason={reason} />
    </div>
  );
}
