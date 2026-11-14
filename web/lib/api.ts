/**
 * The web app's only way to reach the DxP API from the browser (AD-9, AD-14).
 *
 * Requests go to this app's own proxy route, `/api/dxp/<path>`, which adds the
 * `X-DxP-Key` header on the server. The key never reaches the browser, and the
 * browser never sets who the caller is. `<path>` is the API route under
 * `/api/v1`, for example `reports?status=pending` or `runs/run_ab12`.
 *
 * `get` and `post` are generic by response type, so this file does not depend
 * on the generated `lib/types.ts`. Callers name the type:
 *
 *   import type { components } from "@/lib/types";
 *   const run = await get<components["schemas"]["Run"]>(`runs/${id}`);
 *
 * Server components use `lib/server-api.ts` instead (same signatures).
 */

export type QueryValue = string | number | boolean | null | undefined;
export type Query = Record<string, QueryValue>;

/** The API answered with an error status. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly body: unknown;

  constructor(status: number, message: string, code: string | null, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.body = body;
  }
}

/** The API could not be reached at all (network failure, timeout, or a 502/503/504 from the proxy). */
export class ApiUnreachableError extends Error {
  constructor(message = "Couldn't reach the API.") {
    super(message);
    this.name = "ApiUnreachableError";
  }
}

/** True for any failure that means "the API is not there", as opposed to "the API said no". */
export function isUnreachable(error: unknown): boolean {
  return (
    error instanceof ApiUnreachableError ||
    (error instanceof ApiError && [502, 503, 504].includes(error.status))
  );
}

/** Build `path?query`, dropping empty values and a leading slash. */
export function withQuery(path: string, query?: Query): string {
  const clean = path.replace(/^\/+/, "");
  if (!query) return clean;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === null || value === undefined || value === "") continue;
    params.set(key, String(value));
  }
  const qs = params.toString();
  if (!qs) return clean;
  return clean.includes("?") ? `${clean}&${qs}` : `${clean}?${qs}`;
}

/** Turn a fetch Response into the parsed body or an ApiError. Shared with server-api.ts. */
export async function parseResponse<T>(res: Response): Promise<T> {
  const text = await res.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }
  if (!res.ok) {
    if ([502, 503, 504].includes(res.status)) throw new ApiUnreachableError();
    throw new ApiError(res.status, errorMessage(res.status, body), errorCode(body), body);
  }
  return body as T;
}

function errorCode(body: unknown): string | null {
  if (body && typeof body === "object") {
    const o = body as Record<string, unknown>;
    for (const key of ["code", "error"]) {
      if (typeof o[key] === "string") return o[key] as string;
    }
    if (o.detail && typeof o.detail === "object") {
      const d = o.detail as Record<string, unknown>;
      if (typeof d.code === "string") return d.code;
    }
  }
  return null;
}

function errorMessage(status: number, body: unknown): string {
  if (body && typeof body === "object") {
    const o = body as Record<string, unknown>;
    if (typeof o.message === "string") return o.message;
    if (typeof o.detail === "string") return o.detail;
    if (o.detail && typeof o.detail === "object") {
      const d = o.detail as Record<string, unknown>;
      if (typeof d.message === "string") return d.message;
    }
  }
  if (typeof body === "string" && body.length > 0 && body.length < 300) return body;
  return `The API answered with status ${status}.`;
}

const PROXY_BASE = "/api/dxp";

async function request<T>(path: string, init: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${PROXY_BASE}/${path}`, { cache: "no-store", ...init });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === "AbortError") throw cause;
    throw new ApiUnreachableError();
  }
  return parseResponse<T>(res);
}

/** GET an API route by path, for example `get<Report>("reports/abc")`. */
export function get<T>(path: string, query?: Query, init?: RequestInit): Promise<T> {
  return request<T>(withQuery(path, query), { ...init, method: "GET" });
}

/** POST a JSON body to an API route by path. */
export function post<T, B = unknown>(path: string, body?: B, init?: RequestInit): Promise<T> {
  return request<T>(withQuery(path), {
    ...init,
    method: "POST",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

/** List routes return `{ items, next }`; tolerate a bare array too. */
export function itemsOf<T>(page: { items?: T[] } | T[] | null | undefined): T[] {
  if (!page) return [];
  return Array.isArray(page) ? page : (page.items ?? []);
}
