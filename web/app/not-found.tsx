import Link from "next/link";
import { SearchX } from "lucide-react";

import { Notice } from "@/components/shell/notice";
import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-title">Page not found</h1>
      <Notice icon={SearchX} title="There is nothing at this address" role="status">
        Use the Run console, Reports or Audit in the top bar.
      </Notice>
      <div>
        <Link href="/runs" className={buttonVariants({ variant: "default" })}>
          Open the Run console
        </Link>
      </div>
    </div>
  );
}
