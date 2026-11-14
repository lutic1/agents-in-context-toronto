import Link from "next/link";

/**
 * The wordmark "DXP" (brand DNA, concept 03): Manrope 800 in Graphite with the
 * apricot dot from the mark. Text, not an image, so it stays sharp and readable.
 */
export function Wordmark() {
  return (
    <Link
      href="/"
      className="relative rounded-md pr-2.5 text-[22px] font-extrabold leading-none tracking-tight text-foreground"
      aria-label="DXP, home"
    >
      DXP
      <span className="absolute right-0 top-0 size-2 rounded-full bg-apricot" aria-hidden="true" />
    </Link>
  );
}
