import "server-only";

import { connection } from "next/server";

import {
  ApiUnreachableError,
  parseResponse,
  withQuery,
  type Query,
} from "@/lib/api";
import { UpstreamConfigError, upstreamFetch } from "@/lib/server/upstream";

/**
 * `get` and `post` for server components: the same signatures as `lib/api.ts`,
 * calling the API directly with the server-side key (no proxy hop).
 * A missing configuration or an unreachable API both surface as ApiUnreachableError,
 * so a page can render one clear error state.
 */

async function call<T>(path: string, init: Parameters<typeof upstreamFetch>[1]): Promise<T> {
  // Mark the render as request-time before anything can throw. With Cache
  // Components on, a build-time prerender would otherwise run this fetch, fail
  // (no API at build) and bake the error state into the static shell.
  await connection();
  let res: Response;
  try {
    res = await upstreamFetch(path, init);
  } catch (cause) {
    if (cause instanceof UpstreamConfigError) {
      throw new ApiUnreachableError(cause.message);
    }
    throw new ApiUnreachableError();
  }
  return parseResponse<T>(res);
}

export function serverGet<T>(path: string, query?: Query): Promise<T> {
  return call<T>(withQuery(path, query), { method: "GET" });
}

export function serverPost<T, B = unknown>(path: string, body?: B): Promise<T> {
  return call<T>(withQuery(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}
