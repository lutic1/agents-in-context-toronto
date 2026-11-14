import type { components } from "@/lib/types";

type Schemas = components["schemas"];

export type Run = Schemas["Run"];
export type Audit = Schemas["Audit"];
export type AuditEntry = Schemas["AuditEntry"];
export type Grant = Schemas["Grant"];
export type Task = Schemas["Task"];
export type ActionKind = AuditEntry["kind"];
export type ActionStatus = NonNullable<AuditEntry["status"]>;
export type Destination = AuditEntry["destination"];
