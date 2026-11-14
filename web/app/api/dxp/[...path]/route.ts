import { type NextRequest } from "next/server";

import { UpstreamConfigError, upstreamFetch } from "@/lib/server/upstream";

/**
 * The one server route that adds the X-DxP-Key header (AD-14).
 *
 * `/api/dxp/<path>?<query>` is forwarded to `<DXP_API_URL>/api/v1/<path>?<query>`
 * with the reviewer key from the server-only DXP_API_KEY. Only GET and POST are
 * forwarded. A POST must be same-origin JSON (the one exception is the V73 audio path below): a cross-site POST is refused with 403,
 * so another site cannot make a visitor's browser act with the reviewer key. Nothing from the browser decides who the caller is: the browser's own
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

/**
 * True when the request comes from another site. Browsers send Sec-Fetch-Site on every
 * request; Origin is the fallback for those that do not, and is compared with the host
 * this request was addressed to. An absent Origin (curl, server-side callers) is allowed:
 * those are not a visitor's browser being driven by another site.
 */
function isCrossSite(request: NextRequest): boolean {
  if (request.headers.get("sec-fetch-site")?.toLowerCase() === "cross-site") return true;
  const origin = request.headers.get("origin");
  if (origin === null) return false;
  const host = (request.headers.get("x-forwarded-host") ?? request.headers.get("host"))
    ?.split(",")[0]
    .trim()
    .toLowerCase();
  try {
    return !host || new URL(origin).host.toLowerCase() !== host;
  } catch {
    return true; // "null" or an unparseable Origin
  }
}

function mediaType(request: NextRequest): string | undefined {
  return request.headers.get("content-type")?.split(";")[0].trim().toLowerCase();
}

function isJson(request: NextRequest): boolean {
  return mediaType(request) === "application/json";
}

/**
 * V73: the one path that takes a raw audio body instead of JSON. It is matched exactly
 * (`reports/<id>/interview/transcribe`), never by prefix, so every other POST stays JSON-only.
 */
const AUDIO_TYPES = new Set(["audio/webm", "audio/wav"]);
/** About 2 MB: 30 seconds of webm/opus is far smaller, and 16 kHz mono 16-bit wav is under 1 MB. */
const AUDIO_MAX_BYTES = 2 * 1024 * 1024;

function isTranscribePath(path: string[]): boolean {
  return (
    path.length === 4 &&
    path[0] === "reports" &&
    path[1] !== "" &&
    path[2] === "interview" &&
    path[3] === "transcribe"
  );
}

async function forward(request: NextRequest, ctx: Ctx): Promise<Response> {
  const { path } = await ctx.params;
  const audio = request.method === "POST" && isTranscribePath(path);
  if (request.method === "POST") {
    if (isCrossSite(request)) {
      return json(403, "cross_site_blocked", "Cross-site requests are not allowed.");
    }
    if (audio) {
      if (!AUDIO_TYPES.has(mediaType(request) ?? "")) {
        return json(415, "unsupported_media_type", "Recordings must be audio/webm or audio/wav.");
      }
      const declared = Number(request.headers.get("content-length"));
      if (Number.isFinite(declared) && declared > AUDIO_MAX_BYTES) {
        return json(413, "payload_too_large", "That recording is too large.");
      }
    } else if (!isJson(request)) {
      return json(415, "unsupported_media_type", "POST requests must be application/json.");
    }
  }
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
  let body: BodyInit | undefined;
  if (audio) {
    // The audio is forwarded byte for byte and never logged or kept.
    const bytes = await request.arrayBuffer();
    if (bytes.byteLength > AUDIO_MAX_BYTES) {
      return json(413, "payload_too_large", "That recording is too large.");
    }
    body = bytes;
  } else if (hasBody) {
    body = await request.text();
  }
  let res: Response;
  try {
    res = await upstreamFetch(upstreamPath, {
      method: request.method,
      headers,
      body,
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
