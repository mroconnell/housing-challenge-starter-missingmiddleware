# Lessons from the ADU scenario

Written 2026-10-26 by the ADU conductor for the conductors of the next scenarios (transit-oriented density, parking reduction). Read this before your scenario's handover ([TOD_HANDOVER.md](TOD_HANDOVER.md), [PARKING_HANDOVER.md](PARKING_HANDOVER.md)). It records what worked, what didn't, and how the owner (Ryan) likes to work. The ADU decision trail is in [ASSUMPTIONS_AND_QUESTIONS.md](../ASSUMPTIONS_AND_QUESTIONS.md) (AQ-001 to AQ-043 and the decision history table).

## 1. Where the ADU scenario ended up

- **Question answered.** If Wisconsin passed the challenge's benchmark ADU law on 1 January 2027 (stylized), how many additional second-home permits (ADUs plus house-to-duplex conversions on lots that already have a home) would be issued over 2027–2031, compared with current law?
- **Answer (AQ-043).** About 605 permits over five years under current law. The law adds 5,538 (lower, "sluggish adoption"), 8,757 (central, "typical adoption") or 16,889 (strong adoption) permits. The median of eight statewide-law states, applied to Wisconsin, gives 8,851. Sources: `reference/adu_model_statewide.csv`, `reference/adu_model_reference_lines.csv`.
- **Tool.** Seven screens: Wisconsin today, statewide comparison, where (counties, municipalities, Assembly and Senate districts), how sure, why, pilot examples, brief. Run `bash scripts/run_tool.sh`. Packets: [gate3](../gate3/README.md), [gate4](../gate4/README.md), [gate5](../gate5/README.md).

## 2. Method lessons

1. **Statewide evidence first; local detail last.** What moved the ADU answer was other states' experience after a statewide law: California, Washington, Oregon, Maine, Rhode Island, Massachusetts, Utah and Vermont (Chittenden County). Coding local Wisconsin rules for 37 places took a lot of effort. It turned out not to predict activity (AQ-037), and was useful only for pilots and spot checks.
2. **Find a policy taxonomy that separates real reform from weak reform.** The Mercatus Center's 2025 ADU taxonomy (Hamilton and Peterson) was a turning point. It told us which states truly met the benchmark and which passed half-hearted or poison-pilled laws (owner occupancy, discretionary review, parking). Without that, a "statewide law" sample mixes strong and weak laws and the evidence is muddy. If no such report exists for your scenario, build the classification yourself from statute text and from each state's post-law data, and show your work.
3. **Count what happened after the law, per eligible home, by year since the law.** The core evidence was a table: for each statewide-law state, permits per 1,000 eligible homes per year, in years 1, 2, 3… after the law, with the exact source and whether it was read from an official file ("observed") or from a news or vendor figure ("source lead"). See [STATEWIDE_STATES.md](../gate3/STATEWIDE_STATES.md).
4. **Let the data decide, using held-out cases.** Model choices were settled by predicting each state with that state left out and keeping whichever choice predicted better. Examples: California in or out of the common level (G3F-2), units versus permits, eligible-property denominators. The owner prefers this to argument. With few states the test is noisy, so say so (resampling, drop-one checks).
5. **No judgment anchors and no arbitrary multipliers.** The owner rejected a "0.75" anchor, an "80%" new-house adjustment, and a lower scenario built by dividing the central by 1.89. Every level must come from data or a model. For example, the lower scenario is now the average of the two slowest real states, Rhode Island and Oregon.
6. **Scenarios are labelled by meaning, not as statistical intervals.** The three scenarios are "Sluggish adoption" (like the slowest states), "Typical adoption" (like most states) and "Strong adoption" (the high end; only California has gone higher). A median line of the real states is shown as a check. Their info texts say what each means in plain words.
7. **Match the outcome to the benchmark, the same way in every state.** For ADUs this meant:
   - counting a second home on a lot that already has a single-family home;
   - counting teardown-rebuild ADUs but not ADUs built with a new house on a vacant lot (AQ-039);
   - capping counts at 2 per parcel and removing ADUs on apartment lots from California's counts (AQ-041), because California's laws go beyond the benchmark (like condo conversion in Seattle and Austin).
   Expect the same issue for your scenario: other states' counts will include things beyond the benchmark.
8. **Watch the denominator.** Rates are per 1,000 eligible homes, so what is eligible matters. The owner proposed "permits per 1,000 properties eligible under each state's own law". It was tested and predicted worse than per single-family home (ELIGIBLE_BASIS.md), so it became a sensitivity case. Test your denominator the same way.
9. **Ramps come from data.** The law's effect builds over years 1–4. The ramp was measured from the states (about 63%, 80%, 82% and 100% of the full level), not assumed.
10. **A statewide law never subtracts.** Each place's addition is the gap between its rate with the law and its current rate, floored at zero. A city already above the benchmark gets 0, never a cut (the owner's San Diego bonus-ADU example).
11. **Current-law (baseline) rates from measured data where possible.** Use measured permits where they exist (Milwaukee uses its measured rate, not an assumed ramp). The "trace" shows how much rests on observed, estimated and assumed rates. For ADUs, 73% of the addition is in places with assumed current rates. That barely moves the total, but the owner wants it visible.
12. **Sensitivities grouped by what they move.**
    - the law's statewide addition;
    - the baseline only;
    - only where permits land.
    Show each with a plain description. A rules-coding error mostly shifts permits between baseline and addition; say so honestly.
13. **Check transfer to cities like the places you model.** A pre-registered test found that Madison-like cities in Washington and Oregon ran at about half the model's path in years 1–3 ([MADISON_LIKE_CITIES.md](../gate3/MADISON_LIKE_CITIES.md)). Plan a check like this for your scenario. For example, for TOD: do mid-size bus-only cities respond like rail cities?

## 3. Process lessons (gates and agents)

- **The gated plan worked.** Use [MVP_EXECUTION_PLAN.md](../MVP_EXECUTION_PLAN.md): Gate 1 scope and model outline, Gate 2 usable data, Gate 3 baseline/response/uncertainty, Gate 4 working pilot in the tool, Gate 5 statewide MVP and the "good enough" decision. Silence is not approval. Dependent work waits for the owner's decision.
- **Every gate packet** has:
  - what the gate decides and the answer;
  - literal owner review steps;
  - your self-assessment from walking each step yourself;
  - limitations;
  - decisions requested, with one recommendation each.
  Run an independent review or verification agent before presenting. In Gate 4 it found 3 blockers that unit tests missed.
- **Pre-register comparisons** before reading outcomes: the definition, the sample, the rule. Record any later deviations.
- **Work packages:** one agent per package, with exclusive file ownership. The conductor commits per package and pushes to `main` (routine pushes are pre-authorized; D8). Raw data and PDFs never go into git.
- **Decisions go into the AQ log the same day,** with what the owner decided and why. Put the office-hours questions there too.
- **Owner communication** (memory: owner-communication):
  - write every statistic as a full sentence with its unit, numerator and denominator;
  - lead with the answer;
  - keep internal jargon out of what the owner and the tool's users read;
  - one consistent set of terms: say "permit", "unit" and "second home" and stick to them; the owner noticed loose terminology.
- **The tool's audience** is a Wisconsin legislator with no context. Simple at a glance, detail one click away, the chart before the tables, and the plain "what am I looking at" paragraph first.

## 4. Data and compliance lessons

The challenge's data rules are in [CHALLENGE_HANDBOOK.md](../CHALLENGE_HANDBOOK.md). Our audit is in [DATA_COMPLIANCE.md](../DATA_COMPLIANCE.md); owner decisions D1–D6 are there too.
- **Check licences before using a source.** Government records with no licence are accepted as public records (D1). Internet Archive copies are acceptable with care (D2). Commercial mirrors are not acceptable when their terms forbid reuse: the 20 Zoneomics citations had to be replaced.
- **Fetch automatically from the official source.** Avoid hand-typing numbers from PDFs; office-hours question 18 asks whether that counts. Save a raw copy with a `_downloads.json` (URL, date, bytes, SHA-256).
- **Record every dataset in DATA_PROVENANCE.md and DISCLOSURES.md** when it's added, not later.
- **Privacy.** Committed files keep ZIP, city, county and street name only; mask parcel numbers in anything committed. Sample files are masked by `scripts/fetch_samples.py`, and a test checks them.
- **No new dataset without reason.** The owner prefers methods that use data already in the repo, with an outside dataset only as a one-time validation (the LA County assessor check).
- **Dependencies stay permissive.** npm and Python licence checks run in the tests. certifi (MPL-2.0) is the one documented exception. Observable Plot and Vite 8 were avoided for licence reasons.

## 5. Pitfalls we hit

- **Stale local servers.** A `vite preview` on port 4173 from an old worktree made the owner review an old build, and made Playwright reuse it. Playwright now uses port 4317 and never reuses a server. Always confirm the run id in the footer.
- **`.gitignore` hid test fixtures.** The `*.xlsx` rule meant fixtures never reached GitHub, so a fresh clone failed. Test from a fresh clone before calling a gate done.
- **Hard-coded numbers in UI tests and texts** went stale after model reruns. Read numbers from the reference CSVs.
- **Concurrent agents editing the same files.** Give each one exclusive ownership.
- **Partial or provisional years.** Madison's 2026 is a partial year: show it, but don't fit on it.

## 6. Shared pieces

**Already built (owned by the ADU conductor; ask through the coordinator before changing them):**
- **Engine:** `missing_middleware/model/engine.py`, which computes the addition per area and year as `homes × max(y − x, 0) × ramp`, plus the area-paths override.
- **Geography:** area ids, counties, contexts, and the Assembly and Senate district crosswalk (`reference/adu_model_district_crosswalk.csv`).
- **The tool:** `ui/` and the bundle builder `scripts/build_ui_bundle.py`.
- **Compliance scripts and tests:** licence checks, SBOM export and the sample-privacy test.

**To be built by the new sessions and shared between them** (owner's direction, 2026-10-26):
- **All-housing baseline:** all permitted units by area, year and structure type from Census building permits, with a current-law projection for 2027–2031 that reconciles to the state. It is **built by the parking session** and shared with TOD; ADUs can also use it, e.g. as context for the ADU share of all new homes.
- **Multi-scenario tool shell and scenario contract:** a scenario picker, a registry, and a written contract for what files a scenario must produce. It is **built by the TOD session** and shared with parking. The ADU screens must look and behave the same apart from the picker, and the ADU numbers must not change.

Each owner session posts its shared piece's file locations and contract in its thread when ready, and tells the other session through the coordinator. The contract is a starting point, not a fixed format. The owner expects to iterate between tool design and data, and may redesign "by area", or even the ADU screens, so that all scenarios read as one report.

**Policy inventories belong to each session.** Each session researches and owns its own scenario's policy inventory and benchmark classification. A one-off cross-scenario scan done on 2026-10-26 is in [docs/scenarios/STATE_ADOPTION_INVENTORY.md](../scenarios/STATE_ADOPTION_INVENTORY.md). Treat it as unverified starting leads only; many items are marked source_lead.
