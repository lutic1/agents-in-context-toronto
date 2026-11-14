import { ScrollText } from "lucide-react";

import { Section } from "@/components/report/section";

/** The report's script as text, always on the page (V41): the briefing and the avatar video are built from it, and it is the text equivalent of both. */
export function ScriptPanel({ script }: { script: string }) {
  return (
    <Section id="script" icon={ScrollText} title="Report script">
      {script.trim() ? (
        <p className="text-body m-0 max-w-[75ch] whitespace-pre-line break-words">{script}</p>
      ) : (
        <p className="text-body m-0 text-muted-foreground">This report has no script.</p>
      )}
      <p className="text-caption m-0 text-muted-foreground">Built only from this report&apos;s evidence fields.</p>
    </Section>
  );
}
