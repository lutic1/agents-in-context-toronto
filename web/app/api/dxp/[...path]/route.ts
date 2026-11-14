import { type NextRequest } from "next/server";

import { UpstreamConfigError, upstreamFetch } from "@/lib/server/upstream";

/**
 * The one server route that adds the X-DxP-Key header (AD-14).
 *
 * `/api/dxp/<path>?<query>` is forwarded to `<NEXT_PUBLIC_API_URL>/api/v1/<path>?<query>`
 * with the reviewer key from the server-only DXP_API_KEY. Only GET and POST are
 * forwarded. Nothing from the browser decides who the caller is: the browser's own
 * X-DxP-Key, cookies and authorisation headers are never passed on.
 */

const FORWARD_REQUEST_HEADERS = ["content-type", "accept", "range"] as const;
const FORWARD_RESPONSE_HEADERS = [
  "content-type",
  "content-range",
  "accept-ranges",
  "content-disposition",
  "etag",
  "last-modified",
] as const;

type Ctx = { params: Promise<{ path: string[] }> };

function json(status: number, error: string, message: string): Response {
  return Response.json({ error, message }, { status, headers: { "Cache-Control": "no-store" } });
}

async function forward(request: NextRequest, ctx: Ctx): Promise<Response> {
  const { path } = await ctx.params;
  if (path.some((s) => s === "" || s === "." || s === ".." || /[\\/]/.test(s))) {
    return json(400, "bad_path", "That API path is not allowed.");
  }
  const upstreamPath = path.map(encodeURIComponent).join("/") + request.nextUrl.search;

  const headers: Record<string, string> = {};
  for (const name of FORWARD_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers[name] = value;
  }

  const hasBody = request.method === "POST";
  let res: Response;
  try {
    res = await upstreamFetch(upstreamPath, {
      method: request.method,
      headers,
      body: hasBody ? await request.text() : undefined,
    });
  } catch (cause) {
    if (cause instanceof UpstreamConfigError) {
      return json(503, "not_configured", cause.message);
    }
    return json(502, "api_unreachable", "Couldn't reach the API.");
  }

  const out = new Headers({ "Cache-Control": "no-store" });
  for (const name of FORWARD_RESPONSE_HEADERS) {
    const value = res.headers.get(name);
    if (value) out.set(name, value);
  }
  // fetch() has already decoded a compressed body, so the upstream length would be wrong.
  const length = res.headers.get("content-length");
  if (length && !res.headers.get("content-encoding")) out.set("content-length", length);

  const noBody = res.status === 204 || res.status === 304;
  return new Response(noBody ? null : res.body, { status: res.status, headers: out });
}

export const GET = forward;
export const POST = forward;
