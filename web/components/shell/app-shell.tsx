import { Suspense } from "react";

import { Footer } from "@/components/shell/footer";
import { Providers } from "@/components/shell/providers";
import { PageSkeleton } from "@/components/shell/page-skeleton";
import { TissueField } from "@/components/shell/tissue-field";
import { TopBar } from "@/components/shell/top-bar";

/**
 * The shared frame for every page: the tissue field, the glass top bar, one
 * main column inside the content width, and the credits footer.
 *
 * `children` sits inside a Suspense boundary. With Cache Components on, a page
 * that reads request-time data (route params, uncached fetches) must be inside
 * one, and this keeps every later screen from having to add its own just to
 * build. A page with a better skeleton adds its own inside.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <Providers>
      <TissueField />
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-card focus:px-4 focus:py-2 focus:text-table focus:font-semibold"
      >
        Skip to content
      </a>
      <Suspense fallback={<div className="h-16 border-b border-border bg-glass-strong" aria-hidden="true" />}>
        <TopBar />
      </Suspense>
      <main id="main" tabIndex={-1} className="focus:outline-none mx-auto w-full max-w-content flex-1 px-8 py-8">
        <Suspense fallback={<PageSkeleton />}>{children}</Suspense>
      </main>
      <Footer />
    </Providers>
  );
}

