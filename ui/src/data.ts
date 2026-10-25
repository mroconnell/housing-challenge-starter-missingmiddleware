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
  inputs: { path: string; sha256: string }[];
  validation: { passed: number; failed: number; checks: { check: string; passed: boolean; detail: string }[] };
  repo_url: string;
}

export interface Indicator { value: number | null; moe: number | null; status: string; vintage: string; source_id: string }

export interface Scenario {
  id: PathId; label: string; info: string; basis: string; ramp: number[];
  additional_by_year: number[]; additional_total: number; with_law_total: number; with_law_rate_by_year: number[];
}

export interface StateData {
  homes: Indicator;
  housing_units_pep: { year: number; value: number; status: string; vintage: string }[];
  acs_total_units: Indicator; occupied: Indicator; vacant: Indicator; vacancy_rate: Indicator;
  mix: (Indicator & { id: string; label: string })[];
  bps: { year: number; total: number | null; "1unit": number | null; "2_4": number | null; "5plus": number | null; reported_share?: number; vintage?: string }[];
  baseline: {
    by_year: number[]; total: number; low_total: number; high_total: number; low_by_year: number[]; high_by_year: number[];
    bridge_2026: { low: number; central: number; high: number }; rate_per_1000_per_year: number; source: string;
  };
  scenarios: Scenario[];
  reference_line: { label: string; info: string; rate_by_year: number[]; additional_by_year: number[]; additional_total: number; with_law_by_year: number[]; source: string };
  contexts: { id: string; label: string; homes: number; baseline: number; additional_lower: number; additional_central: number; additional_upper: number }[];
}

export interface Area {
  id: string; name: string; county_id: string; county: string; type: string; context: string | null; homes: number;
  x_rate: number | null; x_low: number | null; x_high: number | null; x_status: "observed" | "estimated" | "assumed"; x_basis: string;
  current_class: string; rights_status: "verified" | "source_lead" | "assumed"; rights_added_text: string | null;
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
  id: string; label: string; what: string; change_as_recorded: string; lower: number | null; central: number;
  upper: number | null; difference_central: number; baseline: number; kind: string; source: string; missing_reason: string | null;
}
export interface Uncertainty {
  coverage_rates: { status: string; label: string; areas: number; homes: number; baseline: number; additional_lower: number; additional_central: number; additional_upper: number }[];
  coverage_rights: { status: string; label: string; areas: number; homes: number; additional_central: number }[];
  classes: { id: string; label: string; areas: number; homes: number; baseline: number; additional_lower: number; additional_central: number; additional_upper: number }[];
  sensitivity_cases: SensCase[];
  robustness: { rows: { label: string; adopted: boolean; a: number; b: number; result: string }[]; a_win_share: number; n_states: number; units: string; source: string };
  baseline_sensitivities: { label: string; total: number; change: number }[];
  challenges: { title: string; text: string }[];
}

export interface Pilot {
  slug: string; area_id: string; name: string; county: string; role: "pilot" | "same_market_check"; description: string;
  homes: number; x_rate: number; x_low: number; x_high: number; x_status: string; x_basis: string; current_class: string;
  reform_class: string | null; rights_added_text: string | null; base: number[]; base_low_5yr: number; base_high_5yr: number;
  add: Record<PathId, number[]>; y_rate_y5: Record<PathId, number>;
  permits: { label: string; stage: string; source: string; years: { year: number; units: number | null; permits?: number | null; status: string; reason: string | null }[] };
  measured: { window: string; permits: number; homes: number; thousand_home_years: number; rate: number; lo: number; hi: number; stage: string } | null;
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
  const [manifest, state, areas, uncertainty, pilots, evidence] = await Promise.all([
    getJSON<Manifest>(base + "manifest.json"), getJSON<StateData>(base + "state.json"), getJSON<AreasData>(base + "areas.json"),
    getJSON<Uncertainty>(base + "uncertainty.json"), getJSON<Pilot[]>(base + "pilots.json"), getJSON<Evidence>(base + "evidence.json"),
  ]);
  return { manifest, state, areas, uncertainty, pilots, evidence, base };
}

export const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);
