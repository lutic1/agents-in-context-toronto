import { Skeleton } from "@/components/ui/skeleton";

/** Loading skeleton rows shaped like a titled panel with a few rows (EXPERIENCE "Loading"). */
export function PageSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-6" role="status" aria-label="Loading">
      <Skeleton className="h-9 w-64" />
      <div className="rounded-lg border border-border bg-card p-5">
        <div className="flex flex-col gap-3">
          {Array.from({ length: rows }, (_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </div>
    </div>
  );
}
