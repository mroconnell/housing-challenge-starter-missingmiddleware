// The "In and out of the model" card on a Why tab, shared by ADU and middle housing: the places a reform's rate is
// learned from, grouped, and the places looked at but left out, each with its reason. Every name and reason comes from
// the reform's bundle (evidence_scope); the Summary's "What we modeled" card links to the card's id (?section=<id>).
import { esc } from "./format";

export interface InOutItem { name: string; text: string; note?: string }
export interface InOutGroup { heading: string; testid: string; items: InOutItem[] }

export interface InOutCard {
  /** The card's id (the Summary's link target) and data-testid. */
  id: string;
  intro: string;
  /** The "in" column: one heading and list per group. */
  groups: InOutGroup[];
  /** Shown under the groups, e.g. a check that is not used for the rate. */
  afterGroups?: string;
  out: InOutItem[];
  outHeading: string;
  outTestid?: string;
  source: string;
  /** Links row (already-built HTML). */
  linksHTML?: string;
}

const li = (x: InOutItem) => `<li><strong>${esc(x.name)}</strong>: ${esc(x.text)}${x.note ? `<br><span class="small muted">${esc(x.note)}</span>` : ""}</li>`;

export function inOutCardHTML(c: InOutCard): string {
  const h = `h-${c.id}`;
  return `<section class="card in-out" id="${c.id}" tabindex="-1" aria-labelledby="${h}" data-testid="${c.id}">
    <h2 id="${h}">In and out of the model</h2>
    <p class="muted">${esc(c.intro)}</p>
    <div class="in-out-cols">
      <div data-testid="in-col">
        ${c.groups.map((g) => `<h3>${esc(g.heading)}</h3>
        <ul class="plain in-out-list" data-testid="${g.testid}">${g.items.map(li).join("")}</ul>`).join("")}
        ${c.afterGroups ?? ""}
      </div>
      <div data-testid="out-col">
        <h3>${esc(c.outHeading)}</h3>
        <ul class="plain in-out-list" data-testid="${c.outTestid ?? "out-places"}">${c.out.map(li).join("")}</ul>
      </div>
    </div>
    <p class="small muted" data-testid="in-out-source">Source: ${esc(c.source)}</p>
    ${c.linksHTML ? `<p class="links">${c.linksHTML}</p>` : ""}
  </section>`;
}
