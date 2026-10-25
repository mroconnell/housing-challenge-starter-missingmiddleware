// Number formatting and small DOM helpers. Missing values render as an em dash with a reason, never 0.

export const MISSING = "—";

export function esc(s: unknown): string {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);
}

/** Whole number with thousands separators. */
export function int(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return MISSING;
  return Math.round(v).toLocaleString("en-US");
}

/** Fixed decimals (rates). */
export function dec(v: number | null | undefined, d = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return MISSING;
  return v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
}

export function pct(v: number | null | undefined, d = 0): string {
  if (v === null || v === undefined || Number.isNaN(v)) return MISSING;
  return (v * 100).toFixed(d) + "%";
}

/** Small-area count: whole units, "under 1" below one. */
export function small(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return MISSING;
  if (v > 0 && v < 0.5) return "under 1";
  return int(v);
}

/** A small-area count with its noun: "under 1 permit", "1 permit", "12 permits". */
export function permitsText(v: number | null | undefined): string {
  const t = small(v);
  return `${t} ${t === "under 1" || t === "1" ? "permit" : "permits"}`;
}

/** Small-area value with its range, e.g. "12 (6–23)". */
export function withRange(c: number | null, lo: number | null, hi: number | null): string {
  if (c === null) return MISSING;
  const f = (x: number | null) => (x === null ? MISSING : x > 0 && x < 0.5 ? "<1" : int(x));
  return `${small(c)} (${f(lo)}–${f(hi)})`;
}

export function missing(reason: string): string {
  return `<span class="missing" title="${esc(reason)}">${MISSING}<span class="missing-reason"> ${esc(reason)}</span></span>`;
}

const PILL_LABEL: Record<string, string> = { observed: "Observed", calculated: "Calculated", assumed: "Assumed", estimated: "Calculated" };
const PILL_HELP: Record<string, string> = {
  observed: "Observed: counted in a published source or permit record.",
  calculated: "Calculated: computed by the model from observed inputs and stated rules.",
  estimated: "Calculated: estimated from the average of places with the same coded rules.",
  assumed: "Assumed: a judgment or default where no local data exist.",
};
export function pill(status: string): string {
  const k = status === "estimated" ? "calculated" : status;
  return `<span class="pill pill-${esc(k)}" title="${esc(PILL_HELP[status] ?? status)}"><span class="sr-only">Status: </span>${esc(PILL_LABEL[status] ?? status)}</span>`;
}

export function h(html: string): HTMLElement {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild as HTMLElement;
}

export const YEARS = [2027, 2028, 2029, 2030, 2031];
