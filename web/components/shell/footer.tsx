/** The footer carries the data credits line (NFR11). */
export function Footer() {
  return (
    <footer className="mx-auto w-full max-w-content px-8 pb-8 pt-12">
      <p className="text-caption text-muted-foreground">
        Trial records come from ClinicalTrials.gov. Companion diagnostic approvals come from the
        U.S. FDA list. Synthetic teams, people and corrections are labelled. DxP supports research
        review and gives no medical advice.
      </p>
    </footer>
  );
}
