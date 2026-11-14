/**
 * The page background: a defocused field of stained tissue, drawn in CSS with
 * no image file (DESIGN.md Elevation and Depth). Six very large blurred circles
 * in haematoxylin, eosin and counterstain, fixed behind everything. Text never
 * sits on it directly: it always sits on glass or a white panel.
 */
const BLOBS: { tone: "h" | "e" | "g"; size: number; top: string; left: string }[] = [
  { tone: "h", size: 560, top: "-12%", left: "-8%" },
  { tone: "e", size: 480, top: "8%", left: "58%" },
  { tone: "h", size: 620, top: "52%", left: "70%" },
  { tone: "g", size: 420, top: "60%", left: "8%" },
  { tone: "e", size: 380, top: "78%", left: "40%" },
  { tone: "g", size: 360, top: "-6%", left: "34%" },
];

export function TissueField() {
  return (
    <div className="tissue-field" aria-hidden="true">
      {BLOBS.map((b, i) => (
        <span
          key={i}
          className="tissue-blob"
          data-tone={b.tone}
          style={{ width: b.size, height: b.size, top: b.top, left: b.left }}
        />
      ))}
    </div>
  );
}
