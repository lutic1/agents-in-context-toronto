import "server-only";

import { connection } from "next/server";

import {
  ApiUnreachableError,
  buildPath,
  parseResponse,
  type ApiPath,
  type ResponseOf,
  type RouteArgs,
} from "@/lib/api";
import { UpstreamConfigError, upstreamFetch } from "@/lib/server/upstream";

/**
 * `get` and `post` for server components: the same path-typed signatures as
 * `lib/api.ts`, calling the API directly with the server-side key (no proxy hop).
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

export function serverGet<P extends ApiPath<"get">>(
  route: P,
  ...args: RouteArgs<P, "get">
): Promise<ResponseOf<P, "get">> {
  return call<ResponseOf<P, "get">>(buildPath(route, args[0]), { method: "GET" });
}

export function serverPost<P extends ApiPath<"post">>(
  route: P,
  ...args: RouteArgs<P, "post">
): Promise<ResponseOf<P, "post">> {
  const options = args[0] as { body?: unknown } | undefined;
  return call<ResponseOf<P, "post">>(buildPath(route, options as never), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: options?.body === undefined ? undefined : JSON.stringify(options.body),
  });
}
