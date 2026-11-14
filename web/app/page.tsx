import Link from "next/link";
import { Suspense } from "react";
import { redirect } from "next/navigation";
import { CircleDashed, SquareTerminal } from "lucide-react";

import { ApiError, ApiUnreachableError, itemsOf } from "@/lib/api";
import { serverGet } from "@/lib/server-api";
import { latestRun } from "@/lib/runs";
import { ApiUnreachableNotice, Notice } from "@/components/shell/notice";
import { PageSkeleton } from "@/components/shell/page-skeleton";
import { buttonVariants } from "@/components/ui/button";

/** "/" opens the latest run in the Run console. Without one, it explains what to do. */
export default function Home() {
  return (
    <Suspense fallback={<PageSkeleton rows={2} />}>
      <LatestRunRedirect />
    </Suspense>
  );
}

async function LatestRunRedirect() {
  let target: string | null = null;
  let failure: "unreachable" | "other" | null = null;

  try {
    const page = await serverGet("/runs");
    const latest = latestRun(itemsOf(page));
    if (latest) target = `/runs/${encodeURIComponent(latest.id)}`;
  } catch (error) {
    failure = error instanceof ApiUnreachableError ? "unreachable" : "other";
    if (error instanceof ApiError && error.status >= 500 && error.status !== 501) failure = "unreachable";
  }

  // redirect() throws, so it stays outside the try block.
  if (target) redirect(target);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-title">DxP</h1>
      {failure === "unreachable" ? (
        <ApiUnreachableNotice />
      ) : failure === "other" ? (
        <Notice icon={CircleDashed} title="The run list is not available yet" role="status">
          The API answered, but not with a list of runs. Open the Run console to start a scan.
        </Notice>
      ) : (
        <Notice icon={SquareTerminal} title="No runs yet" role="status">
          Start a scan for the research scope.
        </Notice>
      )}
      <div>
        <Link href="/runs" className={buttonVariants({ variant: "default" })}>
          Open the Run console
        </Link>
      </div>
    </div>
  );
}
