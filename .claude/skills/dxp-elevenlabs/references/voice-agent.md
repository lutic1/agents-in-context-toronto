# ElevenLabs prize options and the voice agent

Checked 12 November 2026. The event page states no criteria for "Best Project Built with ElevenLabs", so the aim is visible, meaningful use of ElevenLabs in the product, not only in the video.

## Options, by value for effort

| Option | What the judge sees | Effort | Status |
|---|---|---|---|
| Audio briefing on each Alert (SKILL.md pattern 1) | Play button on the Alert | 30 to 45 min | Verified |
| "Ask DxP" voice agent grounded in the open Diagnostic's Record | A spoken question answered from MongoDB evidence | 60 to 90 min | Verified, code below |
| Embed widget only, agent built in the dashboard with a knowledge base | A floating voice widget | 20 to 30 min | Verified, snippet below |
| Narrate the demo video with the same voice as the product | Consistent voice in the video | 15 min, no code | Verified (web app or pattern 1) |
| Captions that highlight as the briefing plays | Word-level sync with the Evidence line | 30 to 45 min | Endpoint verified: `POST /v1/text-to-speech/{voice_id}/with-timestamps` returns `audio_base64` and `alignment` (`characters`, `character_start_times_seconds`, `character_end_times_seconds`). SDK method name `UNVERIFIED`: call it over HTTP |
| Reviewer dictates the rejection reason (FR-19) with speech to text | Voice in, Learned rule out | 45 to 60 min | Model IDs `scribe_v3` (batch) and `scribe_v3_live` (real time) verified; SDK calls `UNVERIFIED`. Start at https://elevenlabs.io/docs/eleven-api/guides/cookbooks/speech-to-text |

Do the first row before any other. Take the voice agent only if the demo spine is working.

## Voice agent: the fast path

### 1. Create the agent (dashboard, about 10 minutes, a human does this)

1. ElevenLabs dashboard, Agents, new agent from the Blank template.
2. First message, for example: "I am the DxP assistant, an AI voice. Ask me about this diagnostic."
3. System prompt: answer only from the context supplied in the conversation; quote the source for each fact; say "that is not in the record" when it is not; give no advice about a patient, diagnosis or treatment.
4. Voice tab: pick the same voice as the briefing. Voice model: `eleven_v4_turbo` or `eleven_flash_v2_5`.
5. LLM: new agents default to `gemini-3.5-flash`. Claude Sonnet 4.6 is selectable.
6. Voice settings: attach the pronunciation dictionary (see `pronunciation-dictionary.md`).
7. Security tab: either add an allowlist of hostnames (up to 10, exact match, include `localhost:3000` and the Vercel hostname) or enable authentication and use signed URLs. Configure one, not both.
8. Copy the agent ID (`agent_...`).

The coding-agent route also exists: `npx -y @elevenlabs/cli@latest onboard init` signs in through a browser, writes the key to `.env.local` (or `.env` in Python projects) and creates an agent. A human must approve the sign-in.

### 2. Front end (Next.js, `@elevenlabs/react` 1.22.0)

```bash
npm install @elevenlabs/react
```

```tsx
// app/components/ask-dxp.tsx
"use client";

import { ConversationProvider, useConversation } from "@elevenlabs/react";
import { useCallback } from "react";

function AskDxpInner({ recordContext }: { recordContext: string }) {
  const conversation = useConversation({
    onConnect: () => console.log("agent connected"),
    onDisconnect: () => console.log("agent disconnected"),
    onMessage: (message) => console.log("agent message", message),
    onError: (error) => console.error("agent error", error),
  });

  const start = useCallback(async () => {
    await navigator.mediaDevices.getUserMedia({ audio: true }); // ask for the microphone first
    await conversation.startSession({ agentId: process.env.NEXT_PUBLIC_AGENT_ID! });
    // Adds context without triggering a reply: the Record the user is looking at.
    conversation.sendContextualUpdate(recordContext);
  }, [conversation, recordContext]);

  const connected = conversation.status === "connected";
  return (
    <div>
      <button onClick={start} disabled={connected}>Ask DxP (AI voice)</button>
      <button onClick={() => conversation.endSession()} disabled={!connected}>Stop</button>
      <span>{connected ? (conversation.isSpeaking ? "speaking" : "listening") : conversation.status}</span>
    </div>
  );
}

export function AskDxp({ recordContext }: { recordContext: string }) {
  return (
    <ConversationProvider>
      <AskDxpInner recordContext={recordContext} />
    </ConversationProvider>
  );
}
```

`recordContext` is a compact string built from the Record: field, value, source quote and source URL for each field, plus the latest accepted change. Keep it to a few thousand characters. Build it on the server from MongoDB so the agent answers only from Evidence.

Facts about the SDK that the code relies on:

- `ConversationProvider` must wrap any component that uses the hooks.
- `startSession` needs one of `agentId` (agent open to the public or allowlisted), `signedUrl` (WebSocket) or `conversationToken` (WebRTC). It returns a promise that resolves to the conversation ID.
- `status` is `"disconnected"`, `"connecting"` or `"connected"`. `isSpeaking` is a boolean.
- `sendContextualUpdate(text)` adds context without a reply; `sendUserMessage(text)` sends a typed user turn.
- `textOnly: true` runs without a microphone, useful if the venue is too noisy to demo speech.

### 3. Signed URL (only if authentication is enabled on the agent)

```ts
// app/api/get-signed-url/route.ts
export async function GET() {
  const res = await fetch(
    `https://api.elevenlabs.io/v1/convai/conversation/get-signed-url?agent_id=${process.env.ELEVENLABS_AGENT_ID}`,
    { headers: { "xi-api-key": process.env.ELEVENLABS_API_KEY! } },
  );
  if (!res.ok) return Response.json({ error: "could not get a signed URL" }, { status: 500 });
  const data = await res.json();
  return Response.json({ signedUrl: data.signed_url });
}
```

Then `await conversation.startSession({ signedUrl })` with the value fetched from this route. A signed URL is valid for 15 minutes; a conversation already started continues past that. Request a new one per session. The API key never reaches the browser.

### 4. Let the agent fetch Evidence itself (optional, 20 to 30 minutes more)

Add a Client tool in the agent's Tools section (Tool Type: Client, a name such as `getEvidence`, a String parameter `field`, and tick "Wait for response"). Register a function of the same name in the options passed to `useConversation`:

```tsx
const conversation = useConversation({
  clientTools: {
    getEvidence: async ({ field }: { field: string }) => {
      const res = await fetch(`/api/evidence?diagnosticId=${diagnosticId}&field=${encodeURIComponent(field)}`);
      return await res.text(); // returned to the agent as conversation context
    },
  },
});
```

The name must match the dashboard exactly. Without "Wait for response" the agent does not wait for the result. `/api/evidence` is the project's own route, not an ElevenLabs one.

### 5. Widget only (no React code)

```html
<elevenlabs-convai agent-id="agent-id"></elevenlabs-convai>
<script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async type="text/javascript"></script>
```

Ground it with the agent's Knowledge Base (dashboard, or the API below). Files up to 20 MB (PDF, TXT, DOCX, HTML, EPUB, Markdown); about 300,000 characters fit in the prompt, more needs RAG enabled on the agent.

```python
from elevenlabs import ElevenLabs

elevenlabs = ElevenLabs()  # reads ELEVENLABS_API_KEY
doc = elevenlabs.conversational_ai.knowledge_base.documents.create_from_text(
    text=records_as_text,          # export of the demo Records with their source quotes
    name="DxP lung diagnostics",
)
elevenlabs.conversational_ai.agents.update(
    agent_id="agent_...",
    conversation_config={
        "agent": {"prompt": {"knowledge_base": [{"type": "text", "name": doc.name, "id": doc.id}]}}
    },
)
```

## Limits and rules for the agent

- Billed per minute of conversation; Free includes very little (see SKILL.md). Rehearse with `textOnly` or short sessions, and keep minutes for the recording.
- The use policy requires clear disclosure when people interact with AI. Put "AI voice" in the first message and on the button.
- The policy restricts clinical advice (diagnosis or treatment recommendations) unless overseen by a qualified professional with AI use disclosed. Keep the agent to what the Records and their sources say.
- Do not send patient data or any protected health information. DxP uses open public sources only, so this should never arise.

## Links

- ElevenAgents quickstart: https://elevenlabs.io/docs/eleven-agents/quickstart
- Next.js guide: https://elevenlabs.io/docs/eleven-agents/guides/quickstarts/next-js
- React SDK: https://elevenlabs.io/docs/eleven-agents/libraries/react
- Agent authentication (signed URLs, allowlists): https://elevenlabs.io/docs/eleven-agents/customization/authentication
- Client tools: https://elevenlabs.io/docs/eleven-agents/customization/tools/client-tools
- Knowledge base documents: https://elevenlabs.io/docs/eleven-agents/customization/knowledge-base/manage-documents
- Speech with timestamps: https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps
