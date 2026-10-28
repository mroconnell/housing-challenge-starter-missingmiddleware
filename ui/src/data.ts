// Types for the static bundle written by scripts/build_ui_bundle.py, and the loader.
// The browser never computes a forecast: it only selects, sums and formats bundle values.

export type PathId = "lower" | "central" | "upper";
export const PATHS: PathId[] = ["lower", "central", "upper"];
export type Status = "observed" | "calculated" | "assumed";

export interface DocLink { label: string; path: string; url: string }

export interface Manifest {
  run_id: string;
  scenario_id: string;
  model_status: string;
  title: string;
  outcome: { short: string; long: string; rate_units: string; count_units: string };
  dates: { last_observed_year: number; bridge_year: number; forecast_years: number[]; effective: string };
  vintages: { what: string; vintage: string }[];
  terms: Record<string, string>;
  status_pills: Record<Status, string>;
  limitations: string[];
  pilot_intro: { title: string; text: string; how: string };
  inputs: { path: string; sha256: string }[];
  validation: { passed: number; failed: number; checks: { check: string; passed: boolean; detail: string }[] };
  repo_url: string;
}

export interface Indicator { value: number | null; moe: number | null; status: string; vintage: string; source_id: string }

export interface Scenario {
  /** label: short name ("Central"); name: "central scenario"; chart_label: chart key and table heading;
   *  title + text: editorial description; info: the method (shown in a details disclosure). */
  id: PathId; label: string; name: string; chart_label: string; title: string; text: string; todo: string | null;
  description: string; gate3_label: string; info: string; basis: string; ramp: number[];
  additional_by_year: number[]; additional_total: number; with_law_total: number; with_law_rate_by_year: number[];
}

/** Rates are permits per 1,000 single-family homes per year; values and incomes are homes-weighted geometric means of ACS medians. */
export interface ContextRates { median_home_value: number; median_income: number; x_rate: number; y_rate_2031_central: number; additional_rate_central: number }
export interface ContextRow extends ContextRates {
  id: string; label: string; homes: number; baseline: number; additional_lower: number; additional_central: number; additional_upper: number;
}

export interface StateData {
  homes: Indicator;
  housing_units_pep: { year: number; value: number; status: string; vintage: string }[];
  acs_total_units: Indicator; occupied: Indicator; vacant: Indicator; vacancy_rate: Indicator;
  mix: (Indicator & { id: string; label: string })[];
  bps: { year: number; total: number | null; "1unit": number | null; "2_4": number | null; "5plus": number | null; reported_share?: number; vintage?: string; source_id?: string; source?: string }[];
  /** General housing production: homes permitted per 1,000 housing units (a different denominator from the ADU rates). */
  production_rate: { year: number; value: number; numerator: number; denominator: number; status: string; units: string; source: string; source_id: string };
  acs_period: string; pep_note: string;
  baseline: {
    by_year: number[]; total: number; low_total: number; high_total: number; low_by_year: number[]; high_by_year: number[];
    bridge_2026: { low: number; central: number; high: number }; rate_per_1000_per_year: number; source: string;
  };
  scenarios: Scenario[];
  reference_line: { label: string; n_series: number; carried_forward_years: number[]; info: string; detail: string; why_central_differs: string; rate_by_year: number[]; additional_by_year: number[]; additional_total: number; with_law_by_year: number[]; source: string };
  contexts: ContextRow[];
  /** Why types of place differ (reference/gate5_context_contrast.csv, gate5_model_drivers.csv, gate5_context_examples.csv). */
  context_why: {
    state: ContextRates;
    drivers: { term: "alloc_value_dev" | "value_dev" | "income_dev" | "log_homes"; role: string; coefficient: number; se: number; ratio_10pct: number; meaning: string }[];
    examples: { context: string; name: string; homes: number; median_home_value: number; median_income: number; additional_rate_central: number }[];
    source: string;
  };
  /** Chart-key and table labels shared by every screen and the brief. */
  labels: { baseline: string; band: string; reference: string; added: string };
  page_intro: { compare: string };
}

export interface Area {
  id: string; name: string; county_id: string; county: string; type: string; context: string | null; homes: number;
  x_rate: number | null; x_low: number | null; x_high: number | null; x_status: "observed" | "estimated" | "assumed"; x_basis: string;
  basis_text: string; note?: string; water?: boolean; current_class: string; rights_status: "verified" | "source_lead" | "assumed"; rights_added_text: string | null;
  zoning_status: string | null; base: number[]; base_low_5yr: number | null; base_high_5yr: number | null;
  add: Record<PathId, number[]>; y_rate_y5: Record<PathId, number | null>; pilot: string | null; missing_reason?: string;
}
export interface County {
  id: string; name: string; homes: number; n_areas: number; base: number[]; add: Record<PathId, number[]>;
  homes_by_status: Record<string, number>; context: string | null;
}
export interface AreasData {
  counties: County[]; munis: Area[]; class_short: Record<string, string>; class_text: Record<string, string>;
  x_status_text: Record<string, string>;
}

export interface SensCase {
  id: string; group: "addition" | "baseline" | "local"; label: string; what: string; change_as_recorded: string; lower: number | null; central: number;
  upper: number | null; difference_central: number; baseline: number; kind: string; source: string; missing_reason: string | null;
}
export interface Uncertainty {
  coverage_rates: { status: string; label: string; areas: number; homes: number; baseline: number; additional_lower: number; additional_central: number; additional_upper: number }[];
  coverage_rights: { status: string; label: string; areas: number; homes: number; additional_central: number }[];
  classes: { id: string; label: string; areas: number; homes: number; baseline: number; additional_lower: number; additional_central: number; additional_upper: number }[];
  sensitivity_cases: SensCase[];
  robustness: { rows: { label: string; adopted: boolean; a: number; b: number; result: string }[]; a_win_share: number; n_states: number; units: string; source: string };
  baseline_sensitivities: { label: string; total: number; change: number }[];
  baseline_only: { id: string; label: string; what: string; baseline: number; d_baseline: number; d_additional: number; d_with_law: number; d_additional_lower: number; d_additional_upper: number }[];
  local_effects: { text: string; example: string; not_computed: string };
  sensitivity_groups: Record<"addition" | "baseline" | "local", { title: string; intro: string }>;
  challenges: { title: string; text: string }[];
  /** Central addition by the basis of each place's current-law rate (reference/gate5_trace.csv, places with homes). */
  trace: { status: "observed" | "estimated" | "assumed"; areas: number; homes: number; baseline: number; additional_lower: number; additional_central: number; additional_upper: number }[];
}

export type UnknownId = "like_restricted" | "like_prohibited" | "like_benchmark";
export interface UnknownVariant {
  id: UnknownId; label: string; adopted: boolean; contract_enum: string; run_id: string; x_rate_uncoded: number;
  baseline_total: number; additional_total: Record<PathId, number>; with_law_total: Record<PathId, number>;
  d_baseline: number; d_additional: Record<PathId, number>; d_with_law: Record<PathId, number>;
  baseline_by_year: number[]; additional_by_year: Record<PathId, number[]>; with_law_by_year: Record<PathId, number[]>;
  contexts: { id: string; homes: number; uncoded_homes: number; baseline: number; additional_lower: number; additional_central: number; additional_upper: number }[];
}
type YearVals = { base: number[]; add: Record<PathId, number[]> };
export interface UnknownRules {
  run_group_id: string; uncoded_areas: number; uncoded_homes: number; state_homes: number; default: UnknownId;
  variants: UnknownVariant[];
  /** Per-area and per-county yearly values, only where a variant differs from the adopted run. */
  areas: Partial<Record<UnknownId, Record<string, YearVals>>>;
  counties: Partial<Record<UnknownId, Record<string, YearVals>>>;
  district_note: string; source: string;
}

export interface District {
  id: string; district: string; name: string; homes: number; base: number[]; add: Record<PathId, number[]>;
  n_areas?: number; places?: { id: string; name: string; homes: number; share_of_place: number | null }[]; assembly?: number[];
}
export interface Districts {
  levels: Record<"assembly" | "senate", { rows: District[]; unallocated: District }>;
  caveat: string; method: string; homes_range: [number, number]; boundaries: string; source: string;
}

export interface Pilot {
  slug: string; area_id: string; name: string; county: string; role: "pilot" | "same_market_check"; description: string;
  homes: number; x_rate: number; x_low: number; x_high: number; x_status: string; x_basis: string; basis_text: string; note: string | null; provisional_through: string | null; provisional_detail: string | null; current_class: string;
  reform_class: string | null; rights_added_text: string | null; base: number[]; base_low_5yr: number; base_high_5yr: number;
  add: Record<PathId, number[]>; y_rate_y5: Record<PathId, number>;
  like: { title: string; text: string; detail: string } | null;
  programme: { title: string; text: string; detail: string } | null;
  permits: { label: string; stage: string; source: string; years: { year: number; units: number | null; permits?: number | null; status: string; reason: string | null }[] };
  measured: { window: string; permits: number; homes: number; thousand_home_years: number; rate: number; lo: number | null; hi: number | null; stage: string; used_by_model: boolean } | null;
  rules: { provision: string; value: string | null; from: string | null; to: string | null; source_url: string | null; section: string | null; retrieved: string | null; verification: string; current: boolean }[];
}

export interface Line { name: string; kind: string; points: { k: number; rate: number | null; n?: number }[] }
export interface Evidence {
  cards: { kind: "evidence" | "assumption"; title: string; type: string; status: Status; text: string; challenge?: string;
    table?: { state: string; level: number }[]; table_units?: string; links: DocLink[] }[];
  spaghetti_states: { lines: Line[]; units: string; x_label: string; png: DocLink };
  spaghetti_cities: { lines: Line[]; units: string; x_label: string; png: DocLink };
  docs: DocLink[];
}

export interface Bundle {
  manifest: Manifest; state: StateData; areas: AreasData; uncertainty: Uncertainty; pilots: Pilot[]; evidence: Evidence;
  unknown: UnknownRules; districts: Districts;
  base: string;
}

async function getJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Could not load ${url} (${res.status})`);
  return (await res.json()) as T;
}

export async function loadBundle(): Promise<Bundle> {
  const { run_id } = await getJSON<{ run_id: string }>("runs/latest.json");
  const base = `runs/${run_id}/`;
  const [manifest, state, areas, uncertainty, pilots, evidence, unknown, districts] = await Promise.all([
    getJSON<Manifest>(base + "manifest.json"), getJSON<StateData>(base + "state.json"), getJSON<AreasData>(base + "areas.json"),
    getJSON<Uncertainty>(base + "uncertainty.json"), getJSON<Pilot[]>(base + "pilots.json"), getJSON<Evidence>(base + "evidence.json"),
    getJSON<UnknownRules>(base + "unknown_rules.json"), getJSON<Districts>(base + "districts.json"),
  ]);
  return { manifest, state, areas, uncertainty, pilots, evidence, unknown, districts, base };
}

export const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);
