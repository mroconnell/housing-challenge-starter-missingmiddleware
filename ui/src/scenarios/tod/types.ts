// Bundle types for the transit-oriented density (TOD) reform. Written by scripts/build_tod_bundle.py.
export type ScenId = "little" | "typical" | "strong";
export const SCEN_IDS: ScenId[] = ["little", "typical", "strong"];
export type ByScen = Record<ScenId, number>;

export interface Scenario {
  id: ScenId; label: string; evidence: string; info: string; source: string;
  share_of_stock: number; additional_total: number; with_law_total: number; by_year: number[];
  range_low?: number; range_high?: number;
  /** AQ-054 shared units: extra homes a year statewide; shares of the statewide all-housing baseline and of ACS homes */
  per_year: number; share_of_state_baseline: number; share_of_acs_homes: number;
}
export interface Statewide {
  state_homes: number; stock_homes: number;
  homes_two_cities: { milwaukee: number; madison: number; share: number };
  ladder: { id: string; label: string; stops: number; homes: number; share_of_state: number; main: boolean; context: boolean }[];
  law: { band: string; label: string; height_ft: number; homes_per_acre: number; far: number }[];
  agencies: { agency: string; lines: string; rapid: number; bus15: number; bus20_only: number; main_case: number }[];
  baseline: { years: { year: number; low: number; central: number; high: number }[]; total: number; low_total: number; high_total: number };
  state_baseline_total: number; state_baseline_per_year: number;
  /** Wisconsin's total housing units, ACS 2020–2024 (B25002): the home count for cross-reform figures (AQ-054) */
  acs_homes: number;
  scenarios: Scenario[];
  /** AQ-054: no median line with fewer than min_cases comparable cases */
  median_line: { shown: boolean; min_cases: number; n_studies: number; note: string };
  timing_caveat: string;
}
export interface Muni {
  id: string; name: string; county: string; metro: string; coded: boolean; homes_near: number; share_near: number;
  eligible_acres: number; baseline: number; baseline_low: number; baseline_high: number; add: ByScen; add_years: Record<ScenId, number[]>;
  /** all homes the place is expected to permit under current law, 2027–2031 (shared all-housing baseline) */
  all_baseline: number;
}
export interface AggRow { id: string; name: string; baseline: number; all_baseline: number; add: ByScen }
export interface AggLevel { rows: AggRow[]; total_count: number; all_baseline_total: number }
export interface Areas {
  munis: Muni[];
  metros: { id: string; name: string; places: number; counties: string[]; homes_near: number; baseline: number; all_baseline: number | null; add: ByScen }[];
  counties: AggLevel;
  assembly: AggLevel;
  senate: AggLevel;
  all_baseline_unallocated: number;
  few_homes_places: string[];
  low_permit_places: { name: string; years: number[]; units: number[]; units_5plus: number }[];
}
export interface MapData {
  agencies: string[];
  /** [lon, lat, kind, agency index]; kind r = rail or rapid, b = 15-minute bus, c = 20-minute bus only */
  stops: [number, number, "r" | "b" | "c", number][];
  views: { id: string; label: string; agencies: number[]; bounds: [number, number, number, number] }[];
  outlines: { id: string; name: string | null; tod: boolean; views: string[]; rings: [number, number][][] }[];
  radius_mi: Record<"r" | "b" | "c", number>;
}
export interface SensRow {
  id: string; label: string; text: string; baseline: number; add: Partial<Record<string, number>>;
  milwaukee_metro: number | null; madison_metro?: number; metro_scenario?: string; year_2031?: Partial<ByScen>;
}
export interface HowSure {
  main_baseline: number;
  groups: { id: string; label: string; rows: SensRow[] }[];
  per_acre: { add: ByScen; wisconsin_uncapped: number; wisconsin_capped: number };
  scale: { metro: string; name: string; own_max: number; own_max_year: number; baseline_per_1000: number;
    peak: Record<ScenId, { year: number; total_per_1000: number; exceeds_own_max: boolean }> }[];
  scale_benchmarks: { observed_max: number; observed_max_metro: string; observed_max_year: number; p95: number };
  madison_share: { judged: { share: number; low: number; high: number; homes: number; stock: number }; main: { share: number }; scenarios: ByScen };
  trace: { part: string; status: string; text: string }[];
  cannot_tell: { title: string; text: string }[];
}
export interface Why {
  cases: { id: string; name: string; role: string; role_label: string; estimate: number | null; low: number | null; high: number | null;
    note: string | null; dose_far: number | null; per_far: number | null; per_far_low: number | null; per_far_high: number | null; parking: string | null; mandate: string | null }[];
  classification: { city: string; year: string | null; strength: string; data: string; parking: string; mandate: string; use: string }[];
  strength_counts: Record<string, number>;
  madison: {
    prediction: { value: number; low: number; high: number }; measured: { value: number; low: number; high: number };
    main: { value: number; low: number; high: number }; per_far: { measured: number; low: number; high: number; predicted: number };
    confirmed: boolean;
    years: { year: number; period: string; treatment: { units: number; rate: number; acres: number }; comparison: { units: number; rate: number; acres: number } }[];
    ramp: { label: string; value: number }[];
  };
  sources: { scenario: ScenId; study: string; citation: string; url: string; finding: string; status: string }[];
  city_checks?: { title: string; text: string; doc: { label: string; url: string } }[];
  docs: { label: string; url: string }[];
}
export interface CorridorPlace { name: string; coded: boolean; acres: number; eligible_acres: number; gain_acres: number; existing_homes: number; share_of_place: number; overlay_share: number | null; add_typical: number }
export interface Pilot {
  slug: string; title: string; view: string; city: string; line: string; intro: string; stops: Record<string, number>;
  city_homes: number; city_homes_near: number; city_add: ByScen;
  city_baseline?: number; city_add_years?: Record<ScenId, number[]>;
  corridor?: { places: CorridorPlace[]; add: ByScen; add_years: Record<ScenId, number[]>; acres: number; eligible_acres: number; gain_acres: number; existing_homes: number };
  method?: string;
  zoning_note?: string;
  homes_near_high?: number; city_baseline_all?: number; high_case_acres?: number; reason?: string;
}
export interface Manifest {
  run_id: string; title: string; outcome: { short: string; long: string; rate_units: string; count_units: string };
  dates: { last_observed_year: number; forecast_years: number[]; effective: string };
  vintages: { what: string; vintage: string }[];
  validation: { passed: number; failed: number; checks: { check: string; passed: boolean; detail: string }[] };
  repo_url: string;
}
export interface TodBundle { manifest: Manifest; statewide: Statewide; areas: Areas; map: MapData; howsure: HowSure; why: Why; pilots: Pilot[] }
