/**
 * Avatar video player stub (B01). It renders nothing. B08 replaces this file
 * with the HeyGen avatar video player (Story 10.12): "Render avatar", the
 * Rendering, Ready and Avatar unavailable states, captions on, no autoplay.
 *
 * B04 places `<AvatarPlayer reportId={...} />` on the report page behind the
 * `avatar` flag (lib/features.ts) before B08 exists, so keep this default
 * export and the `reportId` prop when replacing the body.
 */
export type AvatarPlayerProps = {
  reportId: string;
};

export default function AvatarPlayer(props: AvatarPlayerProps): null {
  void props;
  return null;
}
