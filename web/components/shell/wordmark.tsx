import Link from "next/link";

/** The text wordmark "DxP": plain text in the interface face, 700, 22px. No image (D1). */
export function Wordmark() {
  return (
    <Link
      href="/"
      className="rounded-md text-[22px] font-bold leading-none tracking-tight text-foreground"
      aria-label="DxP, home"
    >
      DxP
    </Link>
  );
}
