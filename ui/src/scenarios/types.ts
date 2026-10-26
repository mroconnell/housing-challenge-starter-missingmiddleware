// The contract between the multi-reform shell (ui/src/main.ts) and each reform's screens.
// Written up for people in docs/shared/SCENARIO_CONTRACT.md; keep the two in step.
import registryJson from "./registry.json";

export type ReformStatus = "ready" | "in_development";

/** One row of ui/src/scenarios/registry.json. */
export interface ReformEntry {
  id: string;
  label: string;
  /** Line under the brand in the header: "Wisconsin ADU law · statewide estimates". */
  subtitle: string;
  status: ReformStatus;
  /** Folder under ui/public/ that holds latest.json and runs/<run_id>/ for this reform. */
  bundle_root: string;
  owner: string;
  /** The challenge benchmark text, verbatim. */
  benchmark: string;
  plan_doc: { label: string; path: string } | null;
}

export interface Registry { schema_version: number; default: string; repo_url: string; reforms: ReformEntry[] }

export const REGISTRY = registryJson as Registry;

export function reformEntry(id: string): ReformEntry | undefined {
  return REGISTRY.reforms.find((r) => r.id === id);
}

/** A tab in the screens navigation. `match` is the path prefix that marks the tab current (defaults to `path`). */
export interface Route { path: string; label: string; n: number; match?: string }

/** What the shell gives a reform's screens. Paths are relative to the reform ("/today"), never prefixed. */
export interface ShellEnv {
  entry: ReformEntry;
  /** href for a screen of this reform: "#/today" for the default reform, "#/tod/today" for others. */
  link(path: string): string;
  /** Replace the query part of the current URL (keeps the path; no new history entry). */
  replaceQuery(q: URLSearchParams): void;
  /** Re-render the current screen, keeping scroll position and focus (after a switch changes numbers). */
  refresh(): void;
  /** Say a short message through the page's polite live region. */
  announce(msg: string): void;
}

/** A reform after its data has loaded: the parts of the page it fills. */
export interface MountedReform {
  routes: Route[];
  defaultPath: string;
  /** Short strip under the header (run id, dates). HTML. */
  statusStrip: string;
  /** Footer contents (outcome definition, status key, run id). HTML. */
  footer: string;
  /** Anything else placed after the footer, such as dialogs. HTML. */
  extra: string;
  /** Title suffix for the browser tab: "Wisconsin ADU law". */
  titleSuffix: string;
  /** Called once after the shell has been written to the page (bind dialogs and buttons). */
  bind(): void;
  /** Render one screen into <main>. `params` is the query part of the URL. */
  render(path: string, params: URLSearchParams, main: HTMLElement): void;
  /** Called when the reader switches to another reform (release maps, timers). Optional. */
  leave?(): void;
}

/** A reform's code module: loads its bundle and mounts its screens. */
export interface ReformModule {
  load(entry: ReformEntry): Promise<unknown>;
  mount(env: ShellEnv, data: unknown): MountedReform;
}
