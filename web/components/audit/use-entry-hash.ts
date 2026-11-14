"use client";

import { useEffect, useRef } from "react";

/** The entry a location hash names: `#entry-<decision_id>`, or the bare `#<decision_id>`, decoded. */
function entryTarget(hash: string): HTMLElement | null {
  let id = hash.replace(/^#/, "");
  try {
    id = decodeURIComponent(id);
  } catch {
    // Keep the raw text: it may still match an ID.
  }
  if (!id) return null;
  const el = document.getElementById(id.startsWith("entry-") ? id : `entry-${id}`);
  return el?.hasAttribute("data-audit-entry") ? el : null;
}

/**
 * Opens the entry the address names (`/runs/<run_id>/audit#entry-<decision_id>`, the
 * link a Run console row carries): once the audit has loaded, it scrolls to the entry
 * and puts focus on its heading, so a keyboard or screen reader user lands on it.
 * Scrolling is instant when the person asked for reduced motion (EXPERIENCE "Motion").
 *
 * An entry that is not there yet (the page is still loading, or the stream has not
 * brought it) is looked for again when `entryCount` changes. Each address is handled
 * once, so a refresh never pulls focus back. A later change of the hash, such as the
 * "go to the redraft" link, is handled the same way.
 *
 * @param ready True once the audit has been read and its entries are on screen.
 * @param entryCount How many entries are on screen, so a late arrival is noticed.
 */
export function useEntryHash(ready: boolean, entryCount: number) {
  const handled = useRef<string | null>(null);

  useEffect(() => {
    if (!ready) return;

    const open = () => {
      const hash = window.location.hash;
      if (!hash || handled.current === hash) return;
      const entry = entryTarget(hash);
      if (!entry) return;
      handled.current = hash;
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      entry.scrollIntoView({ block: "start", behavior: reduced ? "auto" : "smooth" });
      entry.querySelector<HTMLElement>("[data-entry-heading]")?.focus({ preventScroll: true });
    };

    open();
    window.addEventListener("hashchange", open);
    return () => window.removeEventListener("hashchange", open);
  }, [ready, entryCount]);
}
