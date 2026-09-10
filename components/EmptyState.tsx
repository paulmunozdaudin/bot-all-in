/**
 * Shared "honest empty state" component. This product never fabricates a
 * prediction, edge, or combination to fill a gap in the UI (brief Section
 * 27) -- when there is nothing real to show, this is what shows instead.
 */
export function EmptyState({ title, reason }: { title: string; reason: string }) {
  return (
    <div className="rounded-lg border border-dashed border-neutral-700 bg-neutral-900/40 p-8 text-center">
      <p className="text-sm font-medium text-neutral-300">{title}</p>
      <p className="mt-2 text-sm text-neutral-500">{reason}</p>
    </div>
  );
}
