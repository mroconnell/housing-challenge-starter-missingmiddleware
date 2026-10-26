# Scenario contract: how a reform plugs into the tool

Written 2026-10-26 by the TOD conductor, who built the multi-reform shell. Status: a starting point, version 1. The owner expects to iterate between tool design and data, so this contract will change; propose changes through the coordinator.

The tool shows one policy reform at a time (ADUs, transit-oriented density, parking requirement reduction). A **reform picker** in the header switches between them. Within a reform, "scenario" keeps its existing meaning: the lower, central and upper (strong adoption) paths. The picker is called the reform picker so the two words never clash.

## 1. What the shell does

- Draws the header (brand, subtitle, reform picker), the status strip, the screens navigation, `<main>`, the live region for announcements, and the footer.
- Routes URLs. The default reform (ADUs) has no prefix, so every existing link keeps working: `#/today`, `#/compare?s=upper`. Other reforms are prefixed with their id: `#/tod/about`. `#/adu/today` also works. The query part belongs to the reform.
- Loads a reform's data the first time it is opened and keeps it for the session.
- Keeps focus and scroll on re-render, moves focus to `<main>` on a new screen, sets the browser tab title, and marks the current tab and the current reform.
- Shows a holding page (benchmark text, link to the plan, no numbers) for any reform whose status is `in_development`.

The browser never computes a forecast. It only selects, sums and formats bundle values.

## 2. Files

| File | Owner | What it is |
| --- | --- | --- |
| `ui/src/main.ts` | shell (TOD conductor) | Header, picker, router |
| `ui/src/scenarios/registry.json` | shell; each reform edits its own entry | The list of reforms |
| `ui/src/scenarios/types.ts` | shell | The TypeScript contract below |
| `ui/src/scenarios/placeholder.ts` | shell | Holding page for reforms in development |
| `ui/src/scenarios/shell.css` | shell | Picker styles |
| `ui/src/scenarios/adu/index.ts` | ADU conductor | ADU status strip, footer, dialog and router |
| `ui/src/screens/*`, `ui/src/data.ts`, `ui/src/app.ts` | ADU conductor | ADU screens and bundle types |
| `ui/src/scenarios/<id>/` | that reform's conductor | Its screens and bundle types |
| `ui/public/<bundle_root>` | that reform's bundle builder | Its JSON bundle |
| `tests/test_reform_registry.py`, `ui/tests/reforms.spec.ts` | shell | Contract tests |

## 3. Registry entry (`ui/src/scenarios/registry.json`)

| Field | Meaning |
| --- | --- |
| `id` | Lower-case URL prefix, for example `tod`. Must not equal an ADU screen segment (`today`, `compare`, `where`, `how-sure`, `why`, `pilot`, `brief`); a test checks this. |
| `label` | The reform's name in the picker and on its pages, for example "Transit-oriented density". |
| `subtitle` | The line under the brand. |
| `status` | `in_development` (holding page, no numbers) or `ready` (its own screens). A reform becomes `ready` only after the owner accepts its Gate 4 pilot. |
| `bundle_root` | Folder under `ui/public/` with `latest.json` and `<run_id>/`. ADUs: `runs/`. New reforms: `scenarios/<id>/runs/`. |
| `owner` | Which conductor owns the reform's files. |
| `benchmark` | The challenge benchmark text, verbatim. A test checks it against `docs/CHALLENGE_SPEC.md`. |
| `plan_doc` | Optional link shown on the holding page: `{label, path}`. |

## 4. Bundle (what a reform's builder writes)

Each reform writes its own bundle under `ui/public/<bundle_root>`, with its own builder script (for example `scripts/build_tod_bundle.py`), so one reform's rerun never rewrites another's files.

- `latest.json`: `{"run_id": "<id>-<hash>"}`.
- `<run_id>/manifest.json` with at least these keys (a test checks every `ready` reform): `run_id`, `scenario_id`, `title`, `outcome` (`short`, `long`, `rate_units`, `count_units`), `dates` (`last_observed_year`, `forecast_years`, `effective`), `vintages`, `validation` (`passed`, `failed`, `checks`), `repo_url`, `inputs` (path and SHA-256 of every input; the run id is a hash of them).
- Any other JSON files the reform's screens need. The ADU bundle (`state.json`, `areas.json`, `uncertainty.json` and others) is the worked example.

Rules carried over from the ADU tool:
- the run id is a hash of the inputs, and the bundle rebuilds byte for byte from the same inputs;
- every displayed number comes from the bundle, and tests read expected numbers from the bundle or from `reference/` CSVs, never hard-coded;
- the builder keeps only the current run in its own folder.

## 5. Code module (`ui/src/scenarios/<id>/index.ts`)

A reform exports a `ReformModule` (see `ui/src/scenarios/types.ts`):

- `load(entry)` fetches its bundle from `entry.bundle_root`.
- `mount(env, data)` returns the parts of the page it fills: `routes` (its tabs), `defaultPath`, `statusStrip`, `footer`, `extra` (for example dialogs), `titleSuffix`, `bind()`, `render(path, params, main)` and an optional `leave()`.
- Links between its screens use `env.link("/where")`, which adds the prefix. State kept in the URL uses `env.replaceQuery(q)`. After a switch changes numbers, call `env.refresh()` and `env.announce("…")`.

Then register the module in the `MODULES` map in `ui/src/main.ts` (ask the shell owner) and set the registry status to `ready`.

## 6. What every reform should be able to show

So that all reforms read as one report, each reform aims to fill the same questions the ADU screens answer, in its own way:

1. **Today:** the current-law baseline for the reform's outcome, with its source year and status.
2. **Statewide comparison:** baseline and three scenarios by year, 2027–2031, labelled by meaning, with a reference line of real cases where there are enough.
3. **Where:** how the addition splits across Wisconsin. The form may differ: TOD may be a list of station areas rather than a map of 1,925 places.
4. **How sure:** sensitivities grouped by what they move, and the trace of what rests on observed, estimated and assumed values.
5. **Why:** the evidence, with "observed" and "source lead" marked.
6. **Pilot examples** and a **brief**.

The outcome may differ by reform but must be stated in the footer (`manifest.outcome.short`). ADUs count second-home permits at issuance; TOD and parking are expected to count all housing units in permits at issuance.

## 7. Guarantees and tests

- The ADU screens, numbers, URLs and tests are unchanged by the shell apart from the picker row in the header. `ui/tests/smoke.spec.ts` and `ui/tests/a11y.spec.ts` run unchanged.
- `ui/tests/reforms.spec.ts` checks the picker, unprefixed and prefixed ADU URLs, and each holding page (benchmark shown, no numbers, back to ADUs).
- `tests/test_reform_registry.py` checks the registry (unique ids, no clash with ADU routes, verbatim benchmarks, plan docs exist) and the core manifest of every `ready` reform.

## 8. Open design questions (for the owner, later)

- Whether to add a cross-reform overview screen once two or more reforms are ready (the policy scenario comparison deliverable could be its print version).
- Whether reforms in development should be hidden from the public build before submission.
- Whether "Wisconsin today" should become shared across reforms, using the all-housing baseline from the parking session.
