import type { components } from "@/lib/types";

/** Shapes the report screens read, named once from the generated schema (A01). */
export type Report = components["schemas"]["Report"];
export type Relationship = components["schemas"]["Relationship"];
export type MemoryUse = components["schemas"]["MemoryUse"];
export type Proposal = components["schemas"]["Proposal"];
export type ReportStatus = Report["status"];
export type NotificationState = NonNullable<Report["notification"]>;
