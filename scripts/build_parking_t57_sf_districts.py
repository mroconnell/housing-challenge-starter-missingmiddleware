"""Test 57 audit addendum 2: San Francisco zoning districts, their parking-minimum history 2003-2018, and the wave A
treated list and clean control list. READS NO OUTCOMES (no permit is read).

    uv run python scripts/build_parking_t57_sf_districts.py

Input (git-ignored): data/raw/parking_t57/sf_zoning_districts.geojson, DataSF "Zoning Map - Zoning Districts"
(3i4a-hu95), PDDL-1.0, from scripts/fetch_parking_t57_gis.py. This layer is CURRENT (2026): the Family Zoning Plan
(Ord. 244-25 map / 245-25 text, operative 2026-01-12) moved some RH/RM lots to RTO-C/RTO-1, some NC/P lots to C-2 and
some P lots to mixed-use or NC. So its polygons are not the 2008/2009 or 2018 boundaries; the area column is today's.

History per district: residential off-street parking minimum, 2003-01-01 to 2018-12-31 (before Ord. 311-18,
effective 2019-01-21), from the ordinances (sfbos.archive.sf.gov PDFs), the SF Planning code-change summaries and the
gocodebook.com mirror of Planning Code Sec. 151.1 history. codelibrary.amlegal.com returned HTTP 403 (not worked
around); gocodebook Sec. 151 pages return 404 (Sec. 151 repealed by Ord. 245-25).
status: verified (sources show no change) / changed / unverifiable / n/a (housing not generally allowed).
role:  control (clean control: verified unchanged) / treated A (wave A) / excluded.
Output: reference/parking_t57_sf_districts.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from missing_middleware import geom as G  # noqa: E402
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW  # noqa: E402

OUT = ROOT / "reference/parking_t57_sf_districts.csv"
B = "https://sfbos.archive.sf.gov/ftp/uploadedfiles/bdsupvrs/ordinances{yy}/o0{n}-{yy}.pdf"
B17 = "https://sfbos.archive.sf.gov/sites/default/files/o0{n}-{yy}.pdf"
GOC = "https://gocodebook.com (SF Planning Code Sec. 151.1 history)"


def o(n: str, yy: str) -> str:
    return (B17 if int(yy) >= 17 else B).format(n=n, yy=yy)


S311, S202 = o("311", "18"), o("202", "18")
WAVE_A_MO = ("treated A (Market-Octavia)", "Ord. 72-08, eff. 2008-05-30: minimum replaced by maximum", "2008")
WAVE_A_EN = ("treated A (Eastern Neighborhoods)", "Ord. 298-08 (with 297-300-08), eff. about 2009-01-19: minimum replaced by maximum", "2009")
NONE = "none: 1 space per unit (Sec. 151) through 2018-12-31; removed only by Ord. 311-18 (2019-01-21)"
EXCL_NOTE = ("use 2018 boundaries; drop lots in Telegraph Hill-North Beach Residential SUD (Ord. 77-10), North of "
             "Market SUD (Ord. 63-11), Market-Octavia and Eastern Neighborhoods plan areas (EN RH/RM lots left out of "
             "both arms), lots rezoned in 2026 (Ord. 244-25); Bernal Heights SUD (Sec. 242) unverified")

# district (zoning label in the layer) -> (status, change, role, land before / note, sources)
H: dict[str, tuple] = {}
for z in ["RH-1(D)", "RH-1", "RH-1(S)", "RH-2", "RH-3", "RM-1", "RM-2", "RM-3", "RM-4"]:
    H[z] = ("verified", NONE, "control", EXCL_NOTE + ("; ZA waiver route for RM added by Ord. 52-15 (2015-05-31)" if z.startswith("RM") else ""),
            f"{S311}; {S202}; Ord. 112-08 summary (080095)")
for z in ["NC-1", "NC-2", "NC-3", "NC-S"]:
    H[z] = ("verified", NONE, "control", EXCL_NOTE + "; waiver route moved to Zoning Administrator by Ord. 63-11 (2011); 2026 P-to-NC lots must be removed",
            f"{S311}; {S202}; {o('175', '12')}; {o('261', '13')}")
for z in ["CASTRO", "INNER CLEMENT", "OUTER CLEMENT", "UPPER FILLMORE", "HAIGHT", "SACRAMENTO", "UNION",
          "24TH-NOE-VALLEY", "WEST PORTAL", "INNER SUNSET"]:
    H[f"NCD-{z}"] = ("verified", NONE, "control", "1987 named NCD; not in any Sec. 151.1 list (2008, 2014, 2018)",
                     f"{S311}; {S202}; {o('227', '14')}")
for z in ["NORIEGA", "IRVING", "TARAVAL", "JUDAH"]:
    H[f"NCD-{z}"] = ("verified", NONE, "control", "was NC-2 until Ord. 175-12 (2012); new table 'Generally, 1 space for each dwelling unit'",
                     o("175", "12"))
for z, prev in [("COLE VALLEY", "NC-1"), ("LAKESIDE VILLAGE", "NC-1"), ("INNER BALBOA STREET", "NC-2"),
                ("OUTER BALBOA STREET", "NC-2"), ("INNER TARAVAL STREET", "NC-2"), ("LOWER HAIGHT STREET", "NC-2"),
                ("CORTLAND AVENUE", "NC-2"), ("SAN BRUNO AVENUE", "NC-2"), ("GEARY BOULEVARD", "NC-3"),
                ("MISSION BERNAL", "NC-3"), ("LOWER POLK STREET", "NC-3")]:
    H[f"NCD-{z}"] = ("verified", NONE, "control", f"was {prev} (1:1) until Ord. 7-20 (2020-03-02)", o("7", "20"))
H["NCD-BAYVIEW"] = ("verified", NONE, "control", "was NC-3 until Ord. 7-20 (2020); also in Bayview Hunters Point Redevelopment Area B (overlay not checked): plausible only",
                    o("7", "20"))
H["NCD-LELAND"] = ("verified", NONE, "control", "was NC-2 until Ord. 23-25 (2025); Schlage Lock SUD Zone 2 frontage follows the normal Planning Code (Ord. 150-14 Sec. 249.45(d))",
                   f"{o('23', '25')}; {o('150', '14')}")
H["NCD-EXCELSIOR"] = ("changed", "Ord. 261-13, eff. 2013-12-27: minimum replaced by maximum of 1 per unit", "excluded",
                      "was NC-1/NC-2/NC-3 and some RH-1 (1:1)", f"{o('261', '13')}; SF Planning case 130084")
H["NCD-JAPANTOWN"] = ("changed", "Ord. 229-15, eff. 2016-01-21: max only", "excluded", "was NC-2/NC-3", o("229", "15"))
H["NCD-POLK"] = ("changed", "Ord. 205-17, eff. 2017-12-03: 'none required'", "excluded", "", o("205", "17"))
H["NCD-PACIFIC"] = H["NCD-POLK"]
H["NCD-BROADWAY"] = ("changed", "Ord. 77-10 (2010-04-26) max only; Ord. 232-14 (2014-12-26) minimums eliminated", "excluded", "",
                     f"{o('77', '10')}; {o('232', '14')}")
H["NCD-NORTH BEACH"] = H["NCD-BROADWAY"]
for z in ["CCB", "CVR", "CRNC"]:
    H[z] = ("changed", "Ord. 77-10 (2010) and Ord. 232-14 (2014-12-26): minimums removed (Chinatown)", "excluded", "",
            f"{o('77', '10')}; {o('232', '14')}")
for z in ["RC-3", "RC-4"]:
    H[z] = ("changed", "Ord. 232-14, eff. 2014-12-26: minimums eliminated (RC-4 North of Market SUD already by Ord. 63-11, 2011)",
            "excluded", "RC-4 minimum was 1 per 4 units before", f"{o('232', '14')}; {o('63', '11')}")
H["C-2"] = ("verified", NONE + " (rate); Washington-Broadway SUD lots: none from Ord. 232-14 (2014)", "control",
            "rate only; exclude Washington-Broadway SUD; 2026 NC/P-to-C-2 lots contaminate current polygons", f"{S311}; {S202}; {o('232', '14')}")
H["NCT-DIVISADERO"] = ("changed", "Divisadero NCD Ord. 227-14 (about 2014-12-07/13); NCT 2015 (Ord. 127-15)", "excluded", "was NC-2", o("227", "14"))
H["NCT-FILLMORE"] = ("changed", "Ord. 228-14, eff. 2014-12-13; NCT 2015 (Ord. 126-15)", "excluded", "was NC-3", o("228", "14"))
H["NCT-OCEAN"] = ("changed", "Balboa Park Ord. 61-09 (about 2009-05-18); expanded onto RH-2/RM-1 by Ord. 209-15 (eff. 2016-01-15)",
                  "excluded", "", f"{o('61', '09')}; {o('209', '15')}")
H["NCT-GLEN PARK"] = ("changed", "Ord. 35-12, eff. 2012-03-22", "excluded", "was NC-2 and others", o("35", "12"))
H["NCT-FOLSOM"] = ("changed", "Ord. 109-11 (2011-07-29) removed minimums; district created by Ord. 42-13 (2013-04-27)", "excluded",
                   "was SoMa RED/RSD/SLR/SLI/SSO", f"SF Planning summary 101350 (Ord. 109-11); {o('42', '13')}")
for z in ["WMUG", "WMUO", "SALI", "RED-MX"]:
    H[z] = H["NCT-FOLSOM"]
H["RED"] = ("changed", "Ord. 109-11, 2011-07-29", "excluded", "", "SF Planning summary 101350 (Ord. 109-11)")
H["M-1"] = ("changed", "Ord. 109-11, 2011: made the same as PDR-1 (max only)", "excluded", "", f"SF Planning summary 101350; {GOC}")
H["NCT-UPPER MARKET"] = ("changed", "Ord. 72-08 (2008-05-30) for the Market-Octavia part; Upper Market NCD remnant outside M-O by Ord. 25-11 (2011-03-24)",
                         WAVE_A_MO[0] + " - 2008 part only", "needs 2008 boundary to separate the 2011 remnant", f"{o('72', '08')}; SF Planning summary 101464")
for z in ["RTO-1", "NCT-3", "NCT-HAYES"]:
    H[z] = ("changed", WAVE_A_MO[1], WAVE_A_MO[0],
            "RTO-1 = old RTO; remove 2026 additions (Ord. 244-25)" if z == "RTO-1" else ("was Hayes-Gough NCD" if z == "NCT-HAYES" else ""),
            o("72", "08"))
for z in ["UMU", "MUG", "MUR", "MUO", "SPD", "RTO-M", "NCT-MISSION", "NCT-24TH-MISSION", "NCT-VALENCIA"]:
    H[z] = ("changed", WAVE_A_EN[1], WAVE_A_EN[0],
            {"MUG": "MUG in Schlage Lock Zone 1 is 2014 (exclude)",
             "NCT-VALENCIA": "date conflict: feasibility CSV lists Valencia St NCT in Ord. 72-08 (2008); the 2026-11-12 code check finds it in Ord. 298-08 (2009); either way wave A",
             }.get(z, ""), o("298", "08"))
H["NCT-SOMA"] = ("changed", "EN part: Ord. 298-08 (2009); Western SoMa part: Ord. 42-13 (2013)", "excluded",
                 "mixed vintage; cannot split with the current layer", f"{o('298', '08')}; {o('42', '13')}")
H["NCT-1"] = ("changed", "Balboa Park Ord. 61-09 (2009) parts; other parts unclear", "excluded", "not created by Market-Octavia", o("61", "09"))
H["NCT-2"] = ("changed", "22nd St (Dogpatch) part: Ord. 298-08 (2009); Geneva Ave part: Ord. 61-09 (2009)", "excluded",
              "mixed; cannot split with the current layer", f"{o('298', '08')}; {o('61', '09')}")
for z in ["C-3-G", "C-3-O", "C-3-R", "C-3-S", "C-3-O(SD)"]:
    H[z] = ("changed", "Ord. 129-06 (2006) max only" + ("; also Ord. 182-12 (2012)" if z == "C-3-O(SD)" else ""), "excluded",
            "always treated (Downtown C-3)", GOC)
for z in ["RH DTR", "SB-DTR", "TB DTR"]:
    H[z] = ("changed", "DTR max only from creation (Ord. 217-05, 2005, and later)", "excluded", "always treated (Rincon Hill/Transbay/South Beach)", GOC)
H["RCD"] = ("changed", "in the Sec. 151.1 max-only list by Aug 2018 (Ord. 202-18); date of change not verified", "excluded",
            "Regional Commercial District (Sec. 758)", S202)
H["CMUO"] = ("changed", "created 2019 (Ord. 296-18); land already max only from 2009/2011/2013", "excluded", "Central SoMa", o("296", "18"))
for z in ["PM-R", "PM-MU1", "PM-MU2", "PM-CF", "PM-OS", "PM-S"]:
    H[z] = ("changed", "Parkmerced SUD Ord. 90-11 with development agreement 89-11 (2011): no minimum, max 1 per unit", "excluded",
            "was RM-1, RM-4, RH-1(D)", f"{o('90', '11')}; gocodebook Sec. 249.64")
H["RTO-C"] = ("unverifiable", "none in window (land was RH/RM), but lots identifiable only from Ord. 244-25 lists", "excluded",
              "new 2026 district", "https://www.sfbos.org/sites/default/files/o0244-25.pdf")
for z in ["MB-O", "MB-RA"]:
    H[z] = ("unverifiable", "set by 1998 Mission Bay redevelopment plan / Design for Development; Planning Code does not apply", "excluded", "", "OCII Mission Bay")
for z in ["TI-MU", "TI-OS", "TI-PCI", "TI-R", "YBI-MU", "YBI-OS", "YBI-PCI", "YBI-R", "Job Corps", "HP-RA"]:
    H[z] = ("unverifiable", "set by plan or development agreement; not checked", "excluded", "", "")
for z in ["P70-MU", "MR-MU", "PPS-MU", "BR-MU", "S-MU"]:
    H[z] = ("unverifiable", "district created after 2015 by development agreement; prior zoning not checked", "excluded", "", "")
for z in ["P", "PDR-1-B", "PDR-1-D", "PDR-1-G", "PDR-2", "M-2"]:
    H[z] = ("n/a", "housing generally not permitted (M-2 not confirmed; M-2 kept Sec. 151 minimum to 2018; PDR-1-D/G max only from 2009)",
            "excluded", "", f"{S202}; {GOC}")


def main() -> None:
    L = G.read_geojson(RAW / "parking_t57/sf_zoning_districts.geojson", columns=["zoning_sim", "zoning", "districtna", "gen", "codesectio"])
    polys = X.polys_to_crs(L.polys, L.crs, X.crs(3310))
    L.attrs["ha"] = G.areas(polys) / 1e4
    g = (L.attrs.groupby(["zoning", "zoning_sim"], dropna=False)
         .agg(name=("districtna", "first"), gen=("gen", "first"), code_section=("codesectio", "first"),
              polygons=("ha", "size"), area_ha_current=("ha", "sum")).reset_index())
    g["area_ha_current"] = g.area_ha_current.round(1)
    out = []
    for _, r in g.iterrows():
        h = H.get(r.zoning)
        if h is None:
            h = ("unverifiable", "not in the code check", "excluded", "", "")
        out.append(dict(zoning=r.zoning, zoning_sim=r.zoning_sim, name=r["name"], gen=r.gen, code_section=r.code_section,
                        polygons=int(r.polygons), area_ha_current=r.area_ha_current, status=h[0],
                        residential_minimum_change_2003_2018=h[1], role=h[2], note=h[3], sources=h[4]))
    d = pd.DataFrame(out)
    d["layer_vintage"] = "current (2026; Family Zoning Plan applied)"
    d = d.sort_values(["role", "zoning"]).reset_index(drop=True)
    d.to_csv(OUT, index=False)
    unk = sorted(set(g.zoning) - set(H))
    print(f"wrote {OUT.relative_to(ROOT)}: {len(d)} districts; not in history table: {unk}")
    print(d.groupby(["role", "status"]).agg(n=("zoning", "size"), ha=("area_ha_current", "sum")).to_string())


if __name__ == "__main__":
    main()
