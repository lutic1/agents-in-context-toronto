# Pronunciation dictionaries

Checked 12 November 2026. Use this only where the text cannot be pre-processed with the `SPOKEN` table in SKILL.md, which in DxP means the voice agent (its LLM writes the words).

## Rules that matter

- Two rule types. **Alias** replaces a spelling with another spelling and works on every model. **Phoneme** (IPA or CMU Arpabet) works only on `eleven_v4`, `eleven_v4_turbo`, `eleven_flash_v2` and `eleven_v3`; other models ignore it silently.
- Matching is case-sensitive and the first matching rule wins. Add a lexeme for each capitalisation that occurs.
- At most 3 dictionaries per text to speech request, applied in order.
- The expanded text is capped at 50 times the input length plus 10,000 characters (400 `pronunciation_dictionary_expansion_too_large`).
- For acronyms, alias rules are enough. Do not spend time on IPA.

## Dictionary file (`dxp.pls`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lexicon version="1.0"
    xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"
    alphabet="ipa" xml:lang="en-US">
  <lexeme><grapheme>ctDNA</grapheme><alias>circulating tumour DNA</alias></lexeme>
  <lexeme><grapheme>cfDNA</grapheme><alias>cell-free DNA</alias></lexeme>
  <lexeme><grapheme>NSCLC</grapheme><alias>non-small cell lung cancer</alias></lexeme>
  <lexeme><grapheme>MRD</grapheme><alias>M R D</alias></lexeme>
  <lexeme><grapheme>EGFR</grapheme><alias>E G F R</alias></lexeme>
  <lexeme><grapheme>PD-L1</grapheme><alias>P D L one</alias></lexeme>
  <lexeme><grapheme>KRAS</grapheme><alias>kay-rass</alias></lexeme>
  <lexeme><grapheme>CDx</grapheme><alias>C D x</alias></lexeme>
  <lexeme><grapheme>Guardant360</grapheme><alias>Guardant three sixty</alias></lexeme>
</lexicon>
```

The spoken forms are suggestions. Confirm each by ear with the chosen voice and model.

## Upload and use (Python)

```python
from elevenlabs import ElevenLabs, PronunciationDictionaryVersionLocator

client = ElevenLabs()  # reads ELEVENLABS_API_KEY

with open("dxp.pls", "rb") as f:
    dictionary = client.pronunciation_dictionaries.create_from_file(
        file=f.read(), name="dxp-lung-diagnostics"
    )

print(dictionary.id, dictionary.version_id)  # keep both; store them in configuration, not in code

audio = client.text_to_speech.convert(
    text="A new ctDNA MRD readout was reported in EGFR-mutant NSCLC.",
    voice_id="YOUR_VOICE_ID",
    model_id="eleven_v4",
    pronunciation_dictionary_locators=[
        PronunciationDictionaryVersionLocator(
            pronunciation_dictionary_id=dictionary.id,
            version_id=dictionary.version_id,
        )
    ],
)
```

If a dictionary is used for the briefing, add `dictionary.version_id` to the cache key in `audio_key`, or a changed dictionary will keep serving old audio.

## Upload and use (TypeScript)

```ts
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import fs from "node:fs";

const client = new ElevenLabsClient();

const dictionary = await client.pronunciationDictionaries.createFromFile({
  file: fs.createReadStream("dxp.pls"),
  name: "dxp-lung-diagnostics",
});

const audio = await client.textToSpeech.convert("YOUR_VOICE_ID", {
  text: "A new ctDNA MRD readout was reported in EGFR-mutant NSCLC.",
  modelId: "eleven_v4",
  pronunciationDictionaryLocators: [
    { pronunciationDictionaryId: dictionary.id, versionId: dictionary.versionId },
  ],
});
```

## Attach to a voice agent

Dashboard: open the agent, Voice settings, add the dictionary, save. In configuration it is `conversation_config.tts.pronunciation_dictionary_locators` (each with `pronunciation_dictionary_id` and `version_id`).

## Not verified

- A REST endpoint creates a dictionary from JSON rules (`POST /v1/pronunciation-dictionaries/add-from-rules`, rules of `type` `alias` or `phoneme` with `string_to_replace`). The SDK method name for it was not seen on an official page: `UNVERIFIED`. Use the file upload above.

## Links

- Guide: https://elevenlabs.io/docs/eleven-api/guides/how-to/text-to-speech/pronunciation-dictionaries
- API reference: https://elevenlabs.io/docs/api-reference/pronunciation-dictionaries/create-from-file
- Agents: https://elevenlabs.io/docs/eleven-agents/customization/voice/pronunciation-dictionary
- Best practices: https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices
