// The estimate card on each reform's Brief tab (owner, 2026-11-12): the 90% range for 2027–2031 with its unit, and the
// "How we count" line from howwecount.ts (the same source as each Summary). It replaces the Introduction's ranges table.
// The ends are always read from the reform's own bundle by the caller, never typed here.
import { esc, int } from "./format";
import { HOW_WE_COUNT, type ReformKey } from "./howwecount";
import { num } from "./range";

export const ESTIMATE_TITLE = "Projected range, 2027–2031 (90%)";

/** A range that dips below zero shows a sign on both ends (minus and plus); otherwise plain whole numbers. */
function ends(low: number, high: number): [string, string] {
  if (low >= 0) return [int(low), int(high)];
  const s = (v: number) => (Math.round(v) > 0 ? `+${int(v)}` : num(v));
  return [s(low), s(high)];
}

/** The card: title, low and high ends with the unit, and the How we count line. */
export function estimateCardHTML(id: ReformKey, r: { low: number; high: number }, unit: string): string {
  const [lo, hi] = ends(r.low, r.high);
  return `<section class="card estimate-card" data-testid="brief-estimate" data-reform="${id}" aria-labelledby="estimate-h-${id}">
    <h2 id="estimate-h-${id}">${esc(ESTIMATE_TITLE)}</h2>
    <p class="estimate-ends">
      <span class="estimate-end"><span class="estimate-end-label">Low end</span> <span class="estimate-num" data-testid="estimate-low">${lo}</span> <span class="estimate-unit">${esc(unit)}</span></span>
      <span class="estimate-end"><span class="estimate-end-label">High end</span> <span class="estimate-num" data-testid="estimate-high">${hi}</span> <span class="estimate-unit">${esc(unit)}</span></span>
    </p>
    <p class="estimate-how" data-testid="estimate-how"><strong>How we count.</strong> ${esc(HOW_WE_COUNT[id])}</p>
  </section>`;
}
