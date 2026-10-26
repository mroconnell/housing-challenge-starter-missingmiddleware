// Shared application state and helpers used by every screen.
import type { Bundle, PathId, Scenario, UnknownId, UnknownVariant } from "./data";
import { esc, int } from "./format";

export const COLORS = {
  baseline: "#4b5450",
  lower: "#2f6db5",
  central: "#17644f",
  upper: "#7b3fb0",
  ref: "#b0501a",
  observed: "#4b5450",
};
export const DASH: Record<string, string | undefined> = { baseline: "7 5", lower: "2 4", central: undefined, upper: "9 3 2 3", ref: "12 4 3 4" };

/** unknown: how places with uncoded local ADU rules are treated (precomputed runs; "like_restricted" is adopted). */
export interface UIState { scenario: PathId; year: number; unknown: UnknownId }

export interface Ctx {
  b: Bundle;
  ui: UIState;
  setScenario(p: PathId): void;
  setUnknown(u: UnknownId): void;
  scen(p?: PathId): Scenario;
  link(path: string): string;
}

export function scenarioLabel(ctx: Ctx, p: PathId): string {
  return ctx.b.state.scenarios.find((s) => s.id === p)!.label;
}

/** The scenario's name in running text: "the central scenario", "the strong adoption scenario". */
export function scenPhrase(ctx: Ctx, p?: PathId): string {
  return `the ${ctx.scen(p).name}`;
}

/** Short form for headings and labels: "central scenario". */
export function scenShort(ctx: Ctx, p?: PathId): string {
  return ctx.scen(p).name;
}

/** Chart-key and table label: "Statewide ADU reform: central scenario" (from the bundle). */
export function scenKey(ctx: Ctx, p?: PathId): string {
  return ctx.scen(p).chart_label;
}

/** A plain-language box with an optional "details" disclosure for the technical background. */
export function infoBox(title: string, text: string, detail?: string, testid = "info-box"): string {
  return `<div class="note-box" role="note" data-testid="${esc(testid)}"><p><strong>${esc(title)}.</strong> ${esc(text)}</p>${detail ? details("Details", `<p class="small">${esc(detail)}</p>`) : ""}</div>`;
}

/** Madison's short note (map details panel); the pilot page uses the longer "Cities like Madison" box. */
export function noteBox(text: string, testid = "madison-note"): string {
  return infoBox("Cities like Madison", text, undefined, testid);
}

/** A native disclosure: detail one click away. */
export function details(summary: string, html: string, cls = ""): string {
  return `<details class="more ${cls}"><summary>${esc(summary)}</summary>${html}</details>`;
}

/** Radio group to choose the highlighted scenario (all three stay visible in charts). */
export function scenarioPicker(ctx: Ctx, name: string, compact = false): string {
  return `<fieldset class="scen-picker ${compact ? "compact" : ""}"><legend>Scenario</legend>${ctx.b.state.scenarios.map((s) => `
    <label class="scen-opt scen-${s.id}">
      <input type="radio" name="${esc(name)}" value="${s.id}" ${ctx.ui.scenario === s.id ? "checked" : ""}>
      <span class="scen-body"><span class="scen-name"><span class="swatch sw-${s.id}" aria-hidden="true"></span>${esc(s.label)}</span>
      ${compact ? "" : `<span class="scen-desc">${esc(s.title)}</span><span class="scen-info">${esc(s.text)}</span><span class="scen-num"><strong>${int(s.additional_total)}</strong> additional permits over 2027–2031</span>`}</span>
    </label>`).join("")}</fieldset>`;
}

export function bindScenarioPicker(ctx: Ctx, root: HTMLElement, name: string): void {
  root.querySelectorAll<HTMLInputElement>(`input[name="${name}"]`).forEach((inp) =>
    inp.addEventListener("change", () => { if (inp.checked) ctx.setScenario(inp.value as PathId); }));
}

export function docLink(l: { label: string; url: string; path: string }): string {
  return `<a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.label)}<span class="sr-only"> (opens GitHub in a new tab)</span> ↗</a>`;
}

export function pilotBanner(role: string): string {
  return `<p class="banner banner-pilot"><strong>Pilot example, not a statewide result.</strong> ${role === "same_market_check"
    ? "Sun Prairie is a same-market check next to Madison."
    : "Pilot pages show how the statewide model plays out in one place."} Pilot figures are already inside the Wisconsin totals and are never added to them.</p>`;
}

/** The modeled statewide benchmark law (challenge handbook text plus AQ-022 and AQ-030). */
export const LAW_TEXT = "The modeled statewide law allows one ADU on every lot with an existing single-family home: detached or semi-detached (attached), at least 600 sq ft, including garage conversions, with no additional parking and no owner-occupancy or related-occupant requirement.";

export function unknownVariant(ctx: Ctx, id?: UnknownId): UnknownVariant {
  return ctx.b.unknown.variants.find((v) => v.id === (id ?? ctx.ui.unknown))!;
}

/** Radio group for the unknown-rules assumption. `disabled` greys it out (district views: adopted run only). */
export function unknownPicker(ctx: Ctx, name: string, disabled = false, note = ""): string {
  const u = ctx.b.unknown;
  return `<fieldset class="unk-picker" ${disabled ? "disabled" : ""} data-testid="unknown-switch"><legend>Places whose local ADU rules we have not coded (${Math.round((u.uncoded_homes / u.state_homes) * 100)}% of single-family homes) behave…</legend>
    ${u.variants.map((v) => `<label><input type="radio" name="${esc(name)}" value="${v.id}" ${(disabled ? v.adopted : ctx.ui.unknown === v.id) ? "checked" : ""}> ${esc(v.label)}</label>`).join("")}
    ${note ? `<p class="small muted" data-testid="unknown-note">${esc(note)}</p>` : ""}</fieldset>`;
}

export function bindUnknownPicker(ctx: Ctx, root: HTMLElement, name: string): void {
  root.querySelectorAll<HTMLInputElement>(`input[name="${name}"]`).forEach((inp) =>
    inp.addEventListener("change", () => { if (inp.checked) ctx.setUnknown(inp.value as UnknownId); }));
}
