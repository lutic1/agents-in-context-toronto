/**
 * Briefing player stub (B01). It renders nothing. B06 replaces this file with
 * the ten-second ElevenLabs briefing player (Story 10.11): the transcript as
 * text, a "Generate briefing" button, then "Play briefing (10 s)".
 *
 * B04 places `<BriefingPlayer reportId={...} />` on the report page behind the
 * `briefing` flag (lib/features.ts) before B06 exists, so keep this default
 * export and the `reportId` prop when replacing the body.
 */
export type BriefingPlayerProps = {
  reportId: string;
};

export default function BriefingPlayer(props: BriefingPlayerProps): null {
  void props;
  return null;
}
