"use client";

import { TriangleAlert } from "lucide-react";

import { Notice } from "@/components/shell/notice";
import { Button } from "@/components/ui/button";

/** A screen that fails to render shows this and keeps the top bar, instead of a blank page. */
export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-title">Something went wrong</h1>
      <Notice icon={TriangleAlert} title="This screen could not be drawn" role="alert">
        Nothing was changed. Try again, or use the top bar to go somewhere else.
      </Notice>
      <div>
        <Button onClick={reset}>Try again</Button>
      </div>
    </div>
  );
}
