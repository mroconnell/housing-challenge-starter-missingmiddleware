# Shared deliverables: status

Written 2026-10-27 by the ADU conductor, who assembles the two shared deliverables (owner-approved). Page estimates assume US Letter, 11-point type, single-spaced: about 550 words of prose a page, with tables taking more room.

## Model & Assumptions Overview ([MODEL_AND_ASSUMPTIONS.md](../MODEL_AND_ASSUMPTIONS.md))

Limit 25 pages. Estimate: about 7,500 words with 9 tables, **16 to 19 pages**.

| Part | Status | Maintained by |
| --- | --- | --- |
| Whole-tool introduction (question, three reforms, horizon, outcome definitions, what is common) | Draft, final numbers | ADU conductor |
| Part A, ADUs | Final (adopted numbers AQ-064, 2026-10-29: baseline 530; lower 6,804 / central 10,629 / upper 19,460; reference line 10,308; all additional permits, 2027–2031) | ADU conductor |
| Part B, parking | Final: word-for-word copy of [parking/MODEL_AND_ASSUMPTIONS_PARKING.md](../parking/MODEL_AND_ASSUMPTIONS_PARKING.md), heading levels changed | Parking session; recopy if the master changes |
| Part C, TOD | Final copy of [tod/MODEL_AND_ASSUMPTIONS_TOD.md](../tod/MODEL_AND_ASSUMPTIONS_TOD.md) at commit 8ea24b0, heading levels changed. **Pending:** two post-check changes await the owner (measured build-up kept unsmoothed; suburbs' placement × 0.719); neither changes the totals. TOD Gate 4 not yet accepted. | TOD session; recopy if the master changes |

Open points:
- The copied parts keep their relative links, which point from `docs/parking/` and `docs/tod/`, so some links in Parts B and C do not resolve from `docs/`. A note at the top of each part says so. Fix by rewriting the link paths when copying, if the owner agrees that this is not a content change.
- The copies must be refreshed whenever a master copy changes.

## Policy Scenario Comparison ([POLICY_SCENARIO_COMPARISON.md](../POLICY_SCENARIO_COMPARISON.md))

Limit 4 pages. Estimate: about 2,100 words with 4 tables, **about 4 pages**, at the limit. If the export runs over, cut the "Against each reform's own baseline" list first.

| Part | Status |
| --- | --- |
| Scenarios addressed, common basis (share of the 122,619-home all-housing baseline; per 1,000 of 2,778,572 existing homes) | Draft |
| ADU facts | Final (AQ-064) |
| Parking facts | Final (confirmed by the parking session 2026-10-27; AQ-046, AQ-048) |
| TOD facts | Final (confirmed by the TOD session 2026-10-27; AQ-044 to AQ-051). **Pending:** the same two post-check changes; neither changes the totals. |
| Ranking, drivers, assumptions that matter, what the tool cannot say | Draft for owner review |

**Re-copying Parts B and C:** run `uv run python scripts/sync_model_doc.py` whenever docs/parking/MODEL_AND_ASSUMPTIONS_PARKING.md or docs/tod/MODEL_AND_ASSUMPTIONS_TOD.md changes. It copies each master verbatim, demotes headings and rewrites links to resolve from docs/.
