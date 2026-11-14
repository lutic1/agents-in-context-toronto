import { Bell, CircleHelp, RefreshCcw, Send, TriangleAlert, type LucideIcon } from "lucide-react";

import { formatTime } from "@/lib/format";
import type { NotificationState } from "@/components/report/types";

/** The Slack alert's state in words with its icon (EXPERIENCE "Run, Slack and general"). Read-only here; Resolve lives in the Run console and Audit view. */
export function alertStateText(notification: NotificationState | null): {
  icon: LucideIcon;
  text: string;
} {
  if (!notification) return { icon: Bell, text: "No Slack alert" };
  const at = notification.posted_at ? ` at ${formatTime(notification.posted_at)}` : "";
  switch (notification.status) {
    case "delivered":
    case "done":
      return { icon: Bell, text: `Slack alert delivered${at}` };
    case "queued":
    case "dispatching":
      return { icon: Send, text: "Slack alert sending" };
    case "failed":
      return { icon: TriangleAlert, text: "Slack alert failed" };
    case "unknown":
      return { icon: CircleHelp, text: "Result unknown. Slack didn't confirm." };
    case "reconciling":
      return { icon: RefreshCcw, text: "Slack alert being checked" };
  }
}

export function AlertState({ notification }: { notification: NotificationState | null }) {
  const { icon: Icon, text } = alertStateText(notification);
  return (
    <span className="inline-flex items-center gap-1.5 text-caption text-muted-foreground">
      <Icon className="size-3.5 shrink-0" strokeWidth={1.75} aria-hidden="true" />
      {text}
    </span>
  );
}
