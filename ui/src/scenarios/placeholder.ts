// Holding page for a reform that is registered but has no estimates yet (status "in_development").
// It shows the benchmark and links to the work in progress; it never shows a number.
import { esc } from "../format";
import { REGISTRY, type MountedReform, type ReformEntry, type ReformModule, type ShellEnv } from "./types";

function docUrl(path: string): string {
  return `${REGISTRY.repo_url}/blob/main/${path}`;
}

function mount(env: ShellEnv): MountedReform {
  const e: ReformEntry = env.entry;
  return {
    routes: [{ path: "/about", label: "About this reform", n: 1 }],
    defaultPath: "/about",
    titleSuffix: `${e.label} (in development)`,
    statusStrip: `<span><strong>In development</strong>: no estimates yet</span>`,
    footer: `<p class="muted"><a href="${esc(REGISTRY.repo_url)}" target="_blank" rel="noopener">Source code and documentation<span class="sr-only"> (opens GitHub in a new tab)</span> ↗</a> · Apache-2.0</p>`,
    extra: "",
    bind() { /* nothing to bind */ },
    render(_path: string, _params: URLSearchParams, main: HTMLElement) {
      main.innerHTML = `
      <h1 data-testid="reform-title">${esc(e.label)}</h1>
      <p class="banner" data-testid="in-development"><strong>In development.</strong> This reform does not have estimates yet. Its numbers will appear here once they have passed review.</p>
      <h2>The benchmark being modelled</h2>
      <blockquote data-testid="benchmark"><p>${esc(e.benchmark)}</p></blockquote>
      <p class="small muted">Benchmark text from the challenge specification.</p>
      ${e.plan_doc ? `<h2>Work in progress</h2><p><a href="${esc(docUrl(e.plan_doc.path))}" target="_blank" rel="noopener">${esc(e.plan_doc.label)}<span class="sr-only"> (opens GitHub in a new tab)</span> ↗</a></p>` : ""}`;
    },
  };
}

export const placeholderReform: ReformModule = { load: () => Promise.resolve(null), mount: (env) => mount(env) };
