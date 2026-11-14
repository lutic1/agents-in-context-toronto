/** Minimal run fields the shell needs. The full `Run` shape comes from the generated types (A01). */
export type RunLike = { id: string; started_at?: string | null; status?: string };

/** The latest run: newest `started_at`, falling back to list order (the API lists newest first). */
export function latestRun<T extends RunLike>(runs: T[]): T | null {
  if (runs.length === 0) return null;
  const dated = runs.filter((r) => r.started_at);
  if (dated.length === 0) return runs[0];
  return dated.reduce((a, b) =>
    new Date(b.started_at as string).getTime() > new Date(a.started_at as string).getTime() ? b : a,
  );
}

/** The principal `GET /whoami` returns (AD-14, D53). */
export type PrincipalLike = {
  id: string;
  name: string;
  kind?: "agent" | "person" | "seed";
  actions?: string[];
};
