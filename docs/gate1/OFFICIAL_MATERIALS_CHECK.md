# Official Materials Check: Housing Data & Technology Innovation Challenge

Checked 2026-10-23 16:39 UTC (12:39 ET) by fetching both pages with curl.

## 1. Sources and how current they are

| Source | Reachable | Freshness marker |
|---|---|---|
| Live Handbook (handbook.html) | Yes, HTTP 200, 21.8 KB | No "last updated" text on the page. HTTP `Last-Modified: Fri, 09 Oct 2026 21:08:09 GMT` |
| Live Official Rules (rules.html) | Yes, HTTP 200, 46.8 KB | No "last updated" text on the page. Same `Last-Modified` (09 Oct 2026) |
| Saved Handbook PDF (repo root, untracked) | Local | Browser print, created 17 Oct 2026 01:51 CEST, 7 pages |
| Team digest `origin/main:docs/CHALLENGE_HANDBOOK.md` | Yes | Says "Last checked 2026-10-16". Last commit a45cc56 (2026-10-17). Matches the local working copy |
| `docs/CHALLENGE_SPEC.md`, `SUBMISSION_CHECKLIST.md` | Local | n/a |

Neither official page has changed since 9 Oct, which is before the digest's check date. Nothing has changed upstream since the team last looked.

## 2. Saved PDF compared with the live Handbook

I compared the two word by word. The text is **identical**. The only differences are navigation chrome, list numbering, and the capitalization of "Administered by / Sponsored by". The PDF is a faithful snapshot.

## 3. Key terms: official text compared with the digest and spec

| Item | Official (Rules prevail over the Handbook) | Digest | Spec / Checklist |
|---|---|---|---|
| Registration | 9:00a ET Sep 14 to 9:00a ET Oct 7, 2026; team composition final at the end of registration | Matches | n/a |
| Coding Period | 9:01a ET **Oct 14** to 11:59p ET **Dec 16, 2026** (the Submission Deadline) | Matches | n/a |
| Judging | Starts at the deadline and ends Jan 30, 2027. Winners announced "on or about February 2027" | Matches | n/a |
| Demo round | Top 5 notified ~Jan 18, 2027. Remote demo Jan 20: 15 min presentation plus 5 min Q&A. Ties go to the higher T&E score, then an independent judge | Matches | n/a |
| Slide deck | ≤30 slides, PDF | Matches | Matches |
| Demo video | Rules: "no longer than five (5) minutes", viewable without an account. Handbook checklist only says "5 minutes" | Says ≤5 min (correct) | Spec says "a 5-minute recording" and the checklist says "5 minutes". Both are looser than the Rules but not contradictory |
| Model & Assumptions | ≤25 pages, single-spaced, with 7 required topics | Matches | Matches. The checklist omits "single-spaced" |
| Scenario comparison | Up to 4 pages, single-spaced, non-technical | Matches | Matches |
| SBOM | Required (Rules 7(d)) and in the Handbook checklist | Listed | **Missing from the spec's Deliverables list.** It appears only in the checklist |
| Eligibility gates | Reproducible setup, tests, no secrets, Dependabot + CodeQL, approved license, public GitHub repo | Matches | Matches |
| Licenses | Apache-2.0 (recommended), MIT, BSD-3, BSD-2. No copyleft, CC0, or Unlicense | Matches | Matches |
| Scoring | T&E 30 / R&S 25 / Usability 20 / Method 15 / Policy 10 | Matches | Matches |
| ADU scenario | One ADU on parcels with existing SF buildings; detached/semi-detached ≥600 sq ft; no additional parking | Matches | Matches |
| Fee scenario | 50% cut across all major categories (planning, environmental review, building, impact); assume $50,000/unit total | Matches | Matches. The $50k assumption sits under "Shared Modeling Assumptions" |
| Missing Middle | 2–6 units, ≤3 stories; teams may assume setbacks and lot coverage do not constrain | **Omits the setback/lot-coverage allowance** | Includes it |
| Horizon / outcome | 5-year horizon. Outcome (permits, starts, completions, stock growth) is the team's choice but must be defined and justified | Matches | Matches |
| Data rules | No large source datasets in the submission; automated acquisition from the authoritative source; no sensitive, restricted, or PII data; describe de-identification and small-cell risk; record provenance (source, version, access date, license, cleaning, limitations) | Matches | **The spec has no data section.** It lacks the automated-acquisition, no-large-data, and no-PII rules |
| Language | Handbook body says "Any memory-safe language". Handbook FAQ says "Any language is acceptable" if the gates pass | Notes the tension correctly | Spec says "Any language is acceptable" and drops the memory-safe wording |
| AI disclosure | Disclose AI codegen tools, pretrained models, external APIs and services, and third-party code, dependencies, and datasets with licenses. AI use is "not be penalized" but unverifiable code scores lower | Matches | Matches |
| Originality | Must be created during the Registration and/or Coding Periods, except disclosed OSS and public data | Matches | Not stated |
| Gallery | Handbook: submissions in general (not just winners) may be featured in a public gallery | Says "Winners may appear", which is slightly narrower | n/a |

## 4. Points relevant to the Wisconsin ADU tool

- **State-level aggregation is required.**
  - Rules 7(a): the baseline and 3 or more scenarios must be "aggregated to the state level".
  - Handbook: smaller geographies are fine "but should aggregate them to the state level".
  - Checklist: "modeled at the state level".
- **A single-state tool appears acceptable.**
  - The framing is about "state-level" reforms, and the Handbook mentions "the chosen jurisdiction" (singular).
  - However, Rules 8 (Policy Insight) says teams that apply their method "to states with less complete data will be judged more favorably than those who model only states with complete datasets".
  - So a single state is allowed, but showing portability to data-poor states is an explicit scoring advantage. That fits the "Replicability & Scalability" criterion and its "plug in alternative datasets" item.
  - Rules 8 (Transparency) also asks for "what data was available in that state, what data was used".
  - **The digest and spec omit both of these points.**
- **Uncertainty is expected.**
  - The Handbook's "What to Avoid" list includes "Point predictions without uncertainty". It prefers estimates, ranges, or sensitivity analyses.
  - Each scenario needs a sensitivity analysis.
  - Methodological Soundness scores the "Reasonableness of sensitivity ranges".
  - The Handbook says precise forecasts matter less than conveying "direction, magnitude, uncertainty, and drivers".
- **Parcel-level precision is a stated pitfall.** State or regional breadth is "prioritized over parcel-level granularity", and tools that trade transparency for precision "will score lower". Parcel data may still be used as an input. This is a caution, not a ban.
- **State-provided data is not required.**
  - There is no requirement to use state-provided data.
  - "Provided data. Teams should use available real-world datasets" lists example types such as satellite data, zoning, parcels, and permits. It does not point to a specific official data package.
  - National sources are "encouraged", and state or local open data portals are on that list.
  - Team-sourced public data is allowed.
  - The Handbook refers to "provided datasets", and the curated dataset list is on the Challenge Platform, which these public pages do not show. **It is unclear whether a provided dataset package exists.**

## 5. Questions for the Administrator (housing.challenge@turnout.rocks)

1. **Single state compared with multiple states.** Is a deep single-state (Wisconsin) tool fully eligible? How much weight does the "states with less complete data" preference carry? Is documenting a method for applying the tool to other states enough, or must a second state actually be run?
2. **"Provided data".** Is there an official provided dataset package, or is the Challenge Platform's curated list only advisory?
3. **Language.** Does "memory-safe" bind? The Handbook body says memory-safe, but the FAQ says any language. Also: is a JS/TS front end with a Python core fine?
4. **Demo video.** Is the limit "≤5 minutes" (as in the Rules) or exactly 5 minutes?
5. **Repo changes after the deadline.** Do they matter? Will judges evaluate a tagged commit as of Dec 16 at 11:59 pm ET? The Rules are silent. The digest already lists this question.
6. **SBOM format.** Is SPDX or CycloneDX expected, and should it be committed to the repo or uploaded? The digest already lists this question.
7. **"Large source datasets".** Is there a size threshold? Is a small committed derived or lookup table (for example, county-level parameters) acceptable?
8. **ADU baseline in Wisconsin.** Many Wisconsin jurisdictions already allow ADUs. Should the scenario be modeled as the marginal change from current local rules? Is the ADU "at least 600 sq ft" a minimum size the policy must allow, or a size teams should assume for modeled units?
9. **Fee scenario.** Should the $50,000/unit apply uniformly even where actual Wisconsin fees are lower, or may teams also show results using local fees?
10. **Submission timing.** Can the team submit early through the platform link to get a pre-deadline compliance review, as Rules 7 implies?

## 6. Recommended team doc fixes (not applied)

- Add the SBOM to the `CHALLENGE_SPEC.md` deliverables.
- Add a data-rules section to the spec: automated acquisition, no large data, no PII.
- Change the video wording in the spec and checklist to "≤5 minutes".
- Add the setback/lot-coverage allowance to the digest.
- Add the Rules 8 "less complete data" preference and the "what data was available in that state" item to the digest and spec.
- Optionally note "single-spaced" for the Model & Assumptions Overview in the checklist.
