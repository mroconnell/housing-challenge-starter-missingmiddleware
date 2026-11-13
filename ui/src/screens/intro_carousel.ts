// "What you'll see" preview carousel on the Introduction (owner 2026-11-11): three small thumbnails of real ADU
// screens, each one link to the full screen. Readability is not the aim (owner: "a tiny preview version that isn't
// really readable"), so each thumbnail is aria-hidden and inert, and the link's name says where it goes.
//
// Every thumbnail is drawn by the screen's own function from the same ADU bundle: no images, no typed numbers.
//   1. drawRangeChart: the Summary tab's band chart (90% range and its chart side lines).
//   2. createMap + defaultCountyView: the Where map's opening view (counties, low end of each county's range).
//   3. againstBandHTML: How sure's "what-ifs against the range" chart (the sensitivity cases).
// The bundle files and the map geometry load only once the carousel scrolls into view. A slide whose data or map
// cannot load shows a short note in place of the thumbnail.
//
// Accessibility (WAI-ARIA APG carousel pattern): a visible Pause/Play button; rotation every 6 seconds stops on
// hover and while focus is inside, and never starts on its own with prefers-reduced-motion; previous, next and
// dot buttons with names; aria-roledescription carousel/slide with "1 of 3" labels; the slide area is a polite
// live region only after the reader moves the slides, never on autoplay; arrow keys move the slides.
import { chartMode } from "../charts";
import type { AreasData, StateData, Uncertainty } from "../data";
import { esc } from "../format";
import { createMap, type GeoKind } from "../map";
import { againstBandHTML, drawRangeChart } from "../range";
import { defaultCountyView } from "./where";

const ADVANCE_MS = 6000;

interface Slide { id: string; caption: string; screen: string; href: string }
const SLIDES: Slide[] = [
  { id: "range", caption: "The ADU projected range, with its comparison scenarios", screen: "Summary", href: "#/summary" },
  { id: "map", caption: "Where ADUs might go: an illustration", screen: "Where", href: "#/where" },
  { id: "sens", caption: "What-ifs against the ADU range", screen: "How sure", href: "#/how-sure" },
];

/** The carousel's markup; `mountIntroCarousel` fills the thumbnails and starts it. */
export function introCarouselHTML(): string {
  const n = SLIDES.length;
  return `<section class="intro-carousel" aria-roledescription="carousel" aria-label="Previews of the ADU screens" data-testid="intro-carousel">
    <div class="ic-slides" id="ic-slides" aria-live="off" aria-atomic="false">
      ${SLIDES.map((s, i) => `<div class="ic-slide${i === 0 ? " is-current" : ""}" role="group" aria-roledescription="slide" aria-label="${i + 1} of ${n}" id="ic-slide-${i}" data-slide="${s.id}" data-testid="intro-slide"${i === 0 ? "" : ' aria-hidden="true"'}>
        <a class="ic-link" href="${s.href}" aria-label="${esc(`${s.caption} — open ${s.screen}`)}" data-testid="intro-slide-link-${s.id}">
          <span class="ic-thumb" aria-hidden="true" inert><span class="ic-thumb-in" data-thumb="${s.id}"><span class="ic-note">Loading the preview…</span></span></span>
          <span class="ic-text"><span class="ic-cap">${esc(s.caption)}</span><span class="ic-go">Open ${esc(s.screen)} <span aria-hidden="true">→</span></span></span>
        </a>
      </div>`).join("")}
    </div>
    <div class="ic-controls">
      <button type="button" class="ic-btn ic-pause" data-testid="intro-carousel-pause" aria-controls="ic-slides">Pause</button>
      <button type="button" class="ic-btn ic-prev" aria-label="Previous preview" aria-controls="ic-slides"><span aria-hidden="true">‹</span></button>
      <span class="ic-dots">${SLIDES.map((s, i) => `<button type="button" class="ic-dot" aria-label="Preview ${i + 1} of ${n}: ${esc(s.caption)}" aria-controls="ic-slide-${i}"${i === 0 ? ' aria-current="true"' : ""}></button>`).join("")}</span>
      <button type="button" class="ic-btn ic-next" aria-label="Next preview" aria-controls="ic-slides"><span aria-hidden="true">›</span></button>
    </div>
  </section>`;
}

async function getJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Could not load ${url} (${res.status})`);
  return (await res.json()) as T;
}

const NOTE = (screen: string) => `<span class="ic-note">Preview not available here. The full chart is on ${esc(screen)}.</span>`;

/** Fill one thumbnail; on any failure the slide keeps a short note and its link. */
async function fill(el: HTMLElement, slide: Slide, job: () => Promise<void> | void): Promise<void> {
  try { await job(); el.dataset.ready = "1"; } catch { el.innerHTML = NOTE(slide.screen); el.dataset.ready = "note"; }
}

async function fillThumbs(root: HTMLElement): Promise<void> {
  const th = (id: string) => root.querySelector<HTMLElement>(`[data-thumb="${id}"]`)!;
  const [sRange, sMap, sSens] = SLIDES;
  let base = "";
  const statePromise = (async () => {
    const { run_id } = await getJSON<{ run_id: string }>("runs/latest.json");
    base = `runs/${run_id}/`;
    return getJSON<StateData>(`${base}state.json`);
  })();
  await Promise.all([
    fill(th("range"), sRange, async () => {
      const s = await statePromise, b = s.baseline;
      const el = th("range");
      el.innerHTML = `<span class="ic-scale"></span>`;
      const years = s.range90.years.map((y) => y.year);
      drawRangeChart(el.firstElementChild as HTMLElement, {
        mode: chartMode(), range: s.range90, sideLines: s.side_lines.filter((x) => x.where === "chart"), noun: "ADU permits",
        base: { years, central: b.by_year, low: b.low_by_year, high: b.high_by_year, prior: { year: 2026, value: b.bridge_2026.central } },
        title: "Preview: second-home permits per year, 2026 to 2031", yLabel: "Permits per year",
        xTicks: [2026, ...years], vline: { x: 2026.5, label: "law takes effect (stylized)" }, height: 300,
      });
    }),
    fill(th("sens"), sSens, async () => {
      const s = await statePromise;
      const u = await getJSON<Uncertainty>(`${base}uncertainty.json`);
      const cases = u.sensitivity_cases.filter((c) => c.id !== "adopted" && c.group === "addition")
        .sort((a, b) => Math.abs(b.difference_central) - Math.abs(a.difference_central));
      th("sens").innerHTML = `<span class="ic-scale">${againstBandHTML(cases.map((c) => ({ label: c.label, value: c.central })), s.range90, "Added ADU permits over 2027–2031", "intro-thumb-sens")}</span>`;
    }),
    fill(th("map"), sMap, async () => {
      const s = await statePromise;
      const [areas, counties] = await Promise.all([getJSON<AreasData>(`${base}areas.json`), getJSON<GeoJSON.FeatureCollection>(`${base}geo_counties.json`)]);
      const empty: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
      const geo: Record<GeoKind, unknown> = { counties, munis: empty, assembly: empty, senate: empty };
      const el = th("map");
      el.innerHTML = `<span class="ic-map"></span>`;
      const m = createMap(el.firstElementChild as HTMLElement, geo, () => {}, () => {}, { preview: true });
      const v = defaultCountyView(s, areas.counties);
      m.setGeography("counties");
      m.setData(v.values, v.breaks);
    }),
  ]);
}

/** Start the carousel inside `main` (after renderIntro). Safe to call when the carousel is absent. */
export function mountIntroCarousel(main: HTMLElement): void {
  const root = main.querySelector<HTMLElement>(".intro-carousel");
  if (!root) return;
  const slidesEl = root.querySelector<HTMLElement>(".ic-slides")!;
  const slides = [...root.querySelectorAll<HTMLElement>(".ic-slide")];
  const dots = [...root.querySelectorAll<HTMLButtonElement>(".ic-dot")];
  const pauseBtn = root.querySelector<HTMLButtonElement>(".ic-pause")!;
  const reduced = (() => { try { return matchMedia("(prefers-reduced-motion: reduce)").matches; } catch { return false; } })();
  let cur = 0;
  let playing = !reduced;           // the reader's choice (Pause/Play); reduced motion starts paused
  let hover = false, focusIn = false;
  let timer: number | undefined;

  const show = (i: number, byUser: boolean) => {
    cur = (i + slides.length) % slides.length;
    // polite only when the reader moved the slides; autoplay never announces
    slidesEl.setAttribute("aria-live", byUser ? "polite" : "off");
    slides.forEach((s, k) => {
      s.classList.toggle("is-current", k === cur);
      if (k === cur) s.removeAttribute("aria-hidden"); else s.setAttribute("aria-hidden", "true");
    });
    dots.forEach((d, k) => { if (k === cur) d.setAttribute("aria-current", "true"); else d.removeAttribute("aria-current"); });
  };
  const running = () => playing && !hover && !focusIn;
  const sync = () => {
    root.dataset.state = playing ? "playing" : "paused";
    pauseBtn.textContent = playing ? "Pause" : "Play";
    pauseBtn.setAttribute("aria-label", playing ? "Pause the previews" : "Play the previews");
    window.clearInterval(timer);
    timer = undefined;
    if (running()) timer = window.setInterval(() => {
      if (!root.isConnected) { window.clearInterval(timer); return; }   // the reader left the Introduction
      show(cur + 1, false);
    }, ADVANCE_MS);
    root.dataset.running = running() ? "1" : "0";
  };

  pauseBtn.addEventListener("click", () => { playing = !playing; if (playing) slidesEl.setAttribute("aria-live", "off"); sync(); });
  root.querySelector(".ic-prev")!.addEventListener("click", () => show(cur - 1, true));
  root.querySelector(".ic-next")!.addEventListener("click", () => show(cur + 1, true));
  dots.forEach((d, k) => d.addEventListener("click", () => show(k, true)));
  root.addEventListener("keydown", (e) => {
    if (!(e.target as HTMLElement).closest(".ic-controls")) return;
    if (e.key === "ArrowRight") { e.preventDefault(); show(cur + 1, true); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); show(cur - 1, true); }
    else return;
    if ((e.target as HTMLElement).classList.contains("ic-dot")) dots[cur].focus();
  });
  root.addEventListener("mouseenter", () => { hover = true; sync(); });
  root.addEventListener("mouseleave", () => { hover = false; sync(); });
  root.addEventListener("focusin", () => { focusIn = true; sync(); });
  root.addEventListener("focusout", (e) => { if (!root.contains(e.relatedTarget as Node | null)) { focusIn = false; sync(); } });
  sync();

  // load the bundle files and the map geometry only once the carousel is on screen
  let started = false;
  const start = () => { if (started) return; started = true; void fillThumbs(root); };
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((es) => { if (es.some((x) => x.isIntersecting)) { io.disconnect(); start(); } });
    io.observe(root);
  } else start();
}
