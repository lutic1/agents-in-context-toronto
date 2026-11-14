/**
 * The web app's only way to reach the DxP API from the browser (AD-9, AD-14).
 *
 * Requests go to this app's own proxy route, `/api/dxp/<path>`, which adds the
 * `X-DxP-Key` header on the server. The key never reaches the browser, and the
 * browser never sets who the caller is.
 *
 * `get` and `post` are typed by path from the generated OpenAPI types
 * (`lib/types.ts`, A01). A path is the route under `/api/v1`, written as the
 * schema writes it, with `{name}` for path parameters. A wrong path, a missing
 * path parameter, a wrong query name or a wrong body fails to compile, and the
 * result type is the route's 200 response:
 *
 *   const run = await get("/runs/{run_id}", { path: { run_id: id } });   // Run
 *   const page = await get("/reports", { query: { status: "pending" } }); // ReportList
 *   await post("/runs", { body: { set: "discover" } });                   // Run
 *
 * There is no untyped escape hatch: every API route is in the schema. If a
 * route is missing, regenerate the types with `npm run gen:types`.
 *
 * Server components use `lib/server-api.ts` instead (same signatures).
 */

import type { paths } from "@/lib/types";

// ---- Types derived from the generated schema -------------------------------

/** The schema keys every route as `/api/v1/...`; the proxy adds that prefix, so callers drop it. */
type Routes = {
  [K in keyof paths as K extends `/api/v1${infer R}` ? R : never]: paths[K];
};

type Method = "get" | "post";

/** Route paths that have the given method. */
export type ApiPath<M extends Method> = {
  [P in keyof Routes]: Routes[P] extends { [K in M]: object } ? P : never;
}[keyof Routes] &
  string;

type Operation<P extends keyof Routes, M extends Method> = NonNullable<Routes[P][M]>;

/** The route's 200 (or 201) JSON response, or `unknown` when it has none (audio, streams). */
export type ResponseOf<P extends ApiPath<M>, M extends Method> =
  Operation<P, M> extends { responses: infer R }
    ? R extends { 200: { content: { "application/json": infer J } } }
      ? J
      : R extends { 201: { content: { "application/json": infer J } } }
        ? J
        : unknown
    : unknown;

type PathParamsOf<O> = O extends { parameters: { path: infer P } } ? P : never;
type QueryOf<O> = O extends { parameters: { query?: infer Q } } ? Exclude<Q, undefined> : never;
type BodyOf<O> = O extends { requestBody?: infer RB }
  ? NonNullable<RB> extends { content: { "application/json": infer B } }
    ? B
    : never
  : never;

type PathPart<O> = [PathParamsOf<O>] extends [never] ? { path?: undefined } : { path: PathParamsOf<O> };
type QueryPart<O> = [QueryOf<O>] extends [never] ? { query?: undefined } : { query?: QueryOf<O> };
type BodyPart<O> = [BodyOf<O>] extends [never]
  ? { body?: undefined }
  : O extends { requestBody: object }
    ? { body: BodyOf<O> }
    : { body?: BodyOf<O> };

/** What a call may or must carry for this route: path parameters, query, and (for POST) the body. */
export type RouteOptions<P extends ApiPath<M>, M extends Method> = PathPart<Operation<P, M>> &
  QueryPart<Operation<P, M>> &
  (M extends "post" ? BodyPart<Operation<P, M>> : { body?: undefined });

/** The options argument is required exactly when the route needs a path parameter or a body. */
export type RouteArgs<P extends ApiPath<M>, M extends Method> = Record<string, never> extends RouteOptions<P, M>
  ? [options?: RouteOptions<P, M>]
  : [options: RouteOptions<P, M>];

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

type LooseOptions = {
  path?: Record<string, unknown>;
  query?: Record<string, unknown>;
  body?: unknown;
};

/**
 * Turn a typed route and its options into `path?query` (no leading slash, path
 * parameters filled in and encoded). Shared by the client, the hook and the server helpers.
 */
export function buildPath(route: string, options?: LooseOptions): string {
  const filled = route.replace(/\{([^}]+)\}/g, (_, name: string) => {
    const value = options?.path?.[name];
    if (value === undefined || value === null || value === "") {
      throw new Error(`Missing path parameter "${name}" for ${route}.`);
    }
    return encodeURIComponent(String(value));
  });
  return withQuery(filled, options?.query as Query | undefined);
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

/** GET a path already built by `buildPath`. For the SWR hook, which keys its cache by that string. */
export function getBuilt<T>(path: string, init?: RequestInit): Promise<T> {
  return request<T>(path, { ...init, method: "GET" });
}

/** GET an API route by path, typed from the schema: `get("/runs/{run_id}", { path: { run_id } })`. */
export function get<P extends ApiPath<"get">>(
  route: P,
  ...args: RouteArgs<P, "get">
): Promise<ResponseOf<P, "get">> {
  return getBuilt<ResponseOf<P, "get">>(buildPath(route, args[0]));
}

/** POST a JSON body to an API route by path, typed from the schema: `post("/runs", { body })`. */
export function post<P extends ApiPath<"post">>(
  route: P,
  ...args: RouteArgs<P, "post">
): Promise<ResponseOf<P, "post">> {
  const options = args[0] as LooseOptions | undefined;
  return request<ResponseOf<P, "post">>(buildPath(route, options), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: options?.body === undefined ? undefined : JSON.stringify(options.body),
  });
}

/** List routes return `{ items, next }`. */
export function itemsOf<T>(page: { items: T[] } | null | undefined): T[] {
  return page?.items ?? [];
}
