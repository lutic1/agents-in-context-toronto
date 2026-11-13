# Live streaming from a Next.js route (TypeScript)

Checked 12 November 2026 with `@elevenlabs/elevenlabs-js` 2.78.0. Use this only if audio must be generated on request. The cached Python path in SKILL.md is the default for DxP.

```ts
// app/api/briefing-stream/route.ts
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

export const runtime = "nodejs";
const elevenlabs = new ElevenLabsClient(); // reads ELEVENLABS_API_KEY

export async function GET(request: Request) {
  const text = new URL(request.url).searchParams.get("text") ?? "";
  if (!text || text.length > 600) {
    return Response.json({ error: "text must be 1 to 600 characters" }, { status: 400 });
  }
  const upstream = await elevenlabs.textToSpeech.stream(process.env.ELEVENLABS_VOICE_ID!, {
    text,
    modelId: process.env.ELEVENLABS_MODEL_ID ?? "eleven_flash_v2_5",
    outputFormat: "mp3_44100_128",
  });
  const body = new ReadableStream({
    async start(controller) {
      for await (const chunk of upstream) controller.enqueue(chunk);
      controller.close();
    },
  });
  return new Response(body, { headers: { "Content-Type": "audio/mpeg" } });
}
```

Play with `<audio controls src={"/api/briefing-stream?text=" + encodeURIComponent(text)} />`. This route spends credits on every play and lets any caller choose the text: keep it out of the deployed demo, or look the text up by Alert ID on the server. `textToSpeech.convert(voiceId, {...})` takes the same options and returns the whole file; `Buffer.from(await new Response(audio).arrayBuffer())` gives the bytes.

## Notes

- The SDK is for server runtimes (Node 18 or later, also Deno, Bun, Cloudflare Workers, Vercel). It is not for the browser: the key would be exposed.
- HTTP streaming returns raw MP3 bytes with chunked transfer encoding. An `<audio>` element pointed at the route starts playing before generation finishes.
- For lowest delay use `eleven_flash_v2_5` or `eleven_v4_turbo` (about 100 ms median model latency). Flash reads numbers, dates and currencies poorly: write them as words.
- Per-request options go in a final argument after the request object, for example `elevenlabs.voices.search({}, { maxRetries: 2, timeoutInSeconds: 30 })`.

## Links

- Streaming guide: https://elevenlabs.io/docs/eleven-api/guides/how-to/text-to-speech/streaming
- Stream speech API reference: https://elevenlabs.io/docs/api-reference/text-to-speech/stream
- Latency: https://elevenlabs.io/docs/eleven-api/guides/how-to/best-practices/latency-optimization
