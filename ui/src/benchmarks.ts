// The challenge's benchmark wording for each reform, word for word from the Participant Handbook (Housing Data and
// Technology Innovation Challenge), "Benchmark Policy Scenarios", "The five scenarios", page 3. Shown in the policy
// box on every reform's Summary tab (ui/src/summary.ts). Checked against the PDF text by
// tests/test_handbook_benchmarks.py; " … " marks a sentence left out of the quote.
import type { ReformKey } from "./howwecount";

export const HANDBOOK_SOURCE = "Participant Handbook, Housing Data and Technology Innovation Challenge: “Benchmark Policy Scenarios”, page 3.";

export const HANDBOOK_BENCHMARK: Record<ReformKey, string> = {
  adu: "Model the effect of allowing one ADU on parcels with existing single-family buildings. Assume detached and semi-detached ADUs of at least 600 square feet are allowed, and no additional parking is required.",
  middle: "Model the effect of allowing 2–6 dwelling units on parcels currently restricted to single-family use, with building heights up to three stories. … Teams may assume that setback and lot coverage requirements do not constrain the development of 2–6 units on a parcel currently restricted to single-family use.",
  tod: "Model the effect of increasing allowable residential density near major transit stops through higher building heights and/or increased floor area ratios. Teams should define major transit stops and justify their transit proximity threshold. Teams may assume that parking requirements are reduced or eliminated.",
  parking: "Model the effects of reducing or eliminating minimum parking requirements for new residential development. Specify assumptions about developer-provided parking in the absence of mandates.",
};
