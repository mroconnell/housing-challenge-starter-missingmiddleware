"""Hand-coded Wisconsin ADU rules (Gate 2). Builder writes reference/wi_adu_rules.csv and wi_rights_exposure.csv.

Verification rule (applied to every row, revised 2026-10-24 after the Gate 2 review):
  verified    = the team read the official document itself: on the official host (municipality, its
                Legistar/agenda site, its ordinance library or code publisher), an archived capture of the
                official host, or the official file re-hosted unchanged (e.g. an ecode360 print PDF).
  source_lead = the text was seen only as a third party's extraction or re-typeset copy: a search-engine
                rendering of a blocked page, a Zoneomics mirror, a snippet, or news.
Classes and restriction flags follow missing_middleware.contracts (owner decision AQ-026, 2026-10-24).
`flags` lists every binding restriction the benchmark reform would remove (restricted places only). A flag
applies only if the provision prevents a benchmark ADU (detached or attached, >= 600 sq ft, by right, no extra
parking, no occupancy rule) on at least some single-family lots. Size: an absolute cap >= 600 sq ft is not a
flag, nor is a cap equal to the house's own size (binds only for houses under 600 sq ft); a percent-of-house
cap below 100%, or a lot-coverage/FAR cap that can fall below 600 sq ft, is `size_below_benchmark`, and the
house size below which it binds is recorded in SIZE_BINDS. `form_limited` = attached-only, detached-only or
conversions-only (both forms by right are part of the benchmark).
"""
R = "2026-10-23"
V, L, U = "verified", "source_lead", "unknown"
BENCH, RESTR, PEXP, PIMP = "scenario_benchmark", "restricted", "prohibited_explicit", "prohibited_implicit"

# (provision, value, effective_from, effective_to, source_url, source_section, verification, notes)
M = []

def muni(ids, name, cls, basis, as_of, added, rules, note="", flags=()):
    M.append(dict(ids=ids, name=name, cls=cls, basis=basis, as_of=as_of, added=added, rules=rules, note=note,
                  flags=list(flags)))

MKE_ORD = "https://milwaukee.legistar1.com/milwaukee/attachments/257d5d3c-c659-463b-8bd3-8d499a6255c2.rtf"
MKE_CPC = "https://milwaukee.legistar1.com/milwaukee/attachments/2caab317-6bf8-4cb3-a0c0-19ed63033977.pdf"
muni(["5507953000", "5513153000", "5513353000"], "Milwaukee city", RESTR, "coded_verified", "2025-08-02",
     "Removes owner-occupancy-at-application rule; otherwise already by right (detached up to 1,300 sq ft, no parking).", [
    ("detached_allowed", "prohibited", "", "2025-08-01", MKE_CPC, "Ch. 295 before File 240999 (ADUs not a defined use; RS: no second principal building)", V, "RT4/RS6 back houses only by special use if pre-2003; RT districts allowed internal/attached 2nd unit as a two-family dwelling where lot area allowed"),
    ("attached_allowed", "prohibited", "", "2025-08-01", MKE_CPC, "Table 295-503-1 (2-family in RS only if legal by 2002-10-01)", V, "prohibited in RS; by right as two-family in RT"),
    ("detached_allowed", "by_right", "2025-08-02", "", MKE_ORD, "File 240999 Sub. 4; Table 295-505-2.5 (limited use)", V, "RS, RT, RM, RO, NS, LB, RB, CS, IM; one ADU per parcel"),
    ("attached_allowed", "by_right", "2025-08-02", "", MKE_ORD, "File 240999 Sub. 4", V, "internal/attached only with a single-family dwelling"),
    ("owner_occupancy", "at_permit", "2025-08-02", "", MKE_ORD, "File 240999 Sub. 4", V, "owner must occupy principal unit at application; exempt if built with new house"),
    ("occupant_restriction", "none", "2025-08-02", "", MKE_ORD, "File 240999 Sub. 4", V, ""),
    ("max_size_sqft", "detached 1300 (or 16% of lot, cap 1600); internal/attached 1000; min 300", "2025-08-02", "", MKE_ORD, "File 240999 Sub. 4", V, ""),
    ("parking_required", "0", "2025-08-02", "", "https://city.milwaukee.gov/DCD/Planning/PlanningAdministration/ZoningResources/Accessory-Dwelling-Units", "DCD ADU page", V, ""),
    ("approval_type", "permitted (limited use standards)", "2025-08-02", "", MKE_ORD, "File 240999 Sub. 4", V, ""),
], flags=["owner_occupancy"])

MAD = "https://legistar.granicus.com/madison/attachments/3bd8ec23-5475-486c-a0fa-c052e688c5b8.pdf"
MAD_68079 = "https://madison.legistar.com/LegislationDetail.aspx?ID=5218928&GUID=692C2A7F-1E48-4779-9367-715C9FD31C50"
# ORD-23-00013 (File 74703, TOD overlay), Second Substitute body (Legistar attachment "74703Body_V5"), read
# 2026-10-24 by plain HTTP, sha256 ef78a3665d93f17f7ccf355e321f77a16c50592123ce7cf19e85a17afb13fc5a
MAD_TOD = "https://legistar2.granicus.com/madison/attachments/e30ec583-ed65-4dd4-97e1-914b3698b269.pdf"
muni(["5502548000"], "Madison city", BENCH, "coded_verified", "2025-10-16",
     "None on most single-family parcels. Edge cases only: (1) the reform extends ADUs to single-family parcels in districts where ADUs are not listed (e.g. LMX, MXC, CC, RMX, THV, downtown/urban and employment districts with houses, PD); (2) it removes replacement parking: outside the TOD overlay and the no-minimum districts the principal house keeps its own 1-space minimum (Table 28I-3), so a garage conversion that removes the only space needs a replacement space.", [
    ("detached_allowed", "conditional", "2013-06-04", "2021-12-15", MAD_68079, "MGO 28.151 (2013 code; ORD-13-00098), as described in File 68079", V, "every ADU a conditional use, owner-occupied, until Dec 2021"),
    ("attached_allowed", "conditional", "2013-06-04", "2021-12-15", MAD_68079, "MGO 28.151 (2013 code; ORD-13-00098), as described in File 68079", V, ""),
    ("approval_type", "conditional", "2013-06-04", "2021-12-15", MAD_68079, "MGO 28.151 (2013 code; ORD-13-00098)", V, "every ADU needed conditional use until Dec 2021"),
    ("approval_type", "permitted", "2021-12-16", "", MAD_68079, "ORD-21-00087 (File 68079)", V, "residential, and mixed-use where single-family allowed; 2021-12-16 to 2024-04-25 by right but owner-occupied (restricted in that period)"),
    ("detached_allowed", "by_right", "2021-12-16", "", MAD, "MGO 28.151", V, ""),
    ("attached_allowed", "by_right", "2021-12-16", "", MAD, "MGO 28.151", V, ""),
    ("owner_occupancy", "ongoing", "2013-06-04", "2024-04-25", "https://webapi.legistar.com/v1/madison/matters/91265/texts/92975", "MGO 28.151 before ORD-24-00022", V, ""),
    ("owner_occupancy", "none", "2024-04-26", "", "https://webapi.legistar.com/v1/madison/matters/91265/texts/92975", "ORD-24-00022 (File 81952)", V, ""),
    ("occupant_restriction", "none", "2021-12-16", "", MAD, "MGO 28.151", V, ""),
    ("max_size_sqft", "1000 (internal; detached building footprint)", "2025-03-08", "", MAD, "ORD-25-00011 (File 86650)", V, "900 sq ft and 2 bedrooms 2021-12-16 to 2025-03-07"),
    ("parking_required", "0", "", "", MAD_TOD, "Table 28I-3 as amended by ORD-23-00013 (File 74703, Second Substitute, Sec. 8); Table 28I-2", V, "ADU automobile minimum 0. The principal single-family detached dwelling keeps a minimum of 1 space ('location only') except in the TOD overlay, the Central area and IG (Table 28I-2, no minimum); so a garage conversion that removes the house's only space needs a replacement space (no ADU-specific exemption read). Later amendments to Table 28I-3 (after 2023) not checked; earlier this row cited a Zoneomics snippet (source lead)"),
    ("other", "one attached ADU, or up to two detached ADUs in one structure", "2025-10-16", "", "https://madison.legistar.com/LegislationDetail.aspx?ID=7656026&GUID=F9768184-E06C-4B82-95BE-E43F79D47E7F", "ORD-25-00068 (File 89918)", V, ""),
    ("other", "ADUs are a listed use in residential districts and in mixed-use/commercial districts where single-family homes are allowed; not listed in some districts that contain single-family parcels (e.g. LMX, MXC, CC, RMX, THV, downtown/urban, employment, PD)", "2021-12-16", "", MAD_68079, "ORD-21-00087 (File 68079); Gate 1 Policy Evidence Map §2.3", V, "edge case for the benchmark: parcel count unknown"),
], note="Benchmark kept by owner decision 2026-10-24 despite two edge cases: replacement parking for the principal house outside the TOD overlay (Table 28I-3, verified from ORD-23-00013) and districts where ADUs are not listed. History: conditional use with owner occupancy until 2021-12-15; by right with owner occupancy 2021-12-16 to 2024-04-25 (restricted in that period); by right without owner occupancy from 2024-04-26 (the observed permit rate from then is the near-benchmark rate).")

GB24 = "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/15619/1400450/pdf"
GB29 = "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/15619/1400449/pdf"
muni(["5500931000"], "Green Bay city", RESTR, "coded_verified", "2025-12-02",
     "ADUs by right instead of conditional use; removes ongoing owner-occupancy rule; removes 1 required parking space.", [
    ("detached_allowed", "conditional", "", "2025-12-01", GB24, "former carriage-house dwelling rule (struck text in G.O. 24-25)", V, "only above a detached rear garage, R-1/RR, lot +2,500 sq ft, owner-occupied, 1 space"),
    ("detached_allowed", "conditional", "2025-12-02", "", GB29, "G.O. 29-25, Table 44-1 ('C' in R-1, R-2, R-3, RR)", V, "publication date not seen"),
    ("attached_allowed", "conditional", "2025-12-02", "", GB24, "G.O. 24-25, §44-1580(f)", V, ""),
    ("owner_occupancy", "ongoing", "2025-12-02", "", GB24, "§44-1580(f)", V, ""),
    ("occupant_restriction", "none", "2025-12-02", "", GB24, "§44-1580(f)", V, "short-term rental prohibited"),
    ("max_size_sqft", "lesser of 1000 or size of primary building", "2025-12-02", "", GB24, "§44-1580(f)", V, ""),
    ("parking_required", "1", "2025-12-02", "", GB24, "§44-1580(f)", V, ""),
    ("approval_type", "conditional use permit", "2025-12-02", "", GB29, "Table 44-1", V, ""),
], flags=["discretionary_review", "owner_occupancy", "extra_parking"])

KEN = "https://library.municode.com/wi/kenosha/codes/zoning_ordinance"
muni(["5505939225"], "Kenosha city", RESTR, "coded_source_lead", "2026-04-20",
     "Detached and attached ADUs by right in all single-family districts for any occupant; removes the domestic-help occupant limit and the one-principal-building bar; at least 600 sq ft despite the 840 sq ft / 15% accessory cap; no extra parking.", [
    ("detached_allowed", "unknown", "", "", KEN, "§3.04.A.4 (RS-1 permitted principal use: residential quarters for domestic help)", L, "borderline: a permitted principal use in RS-1 only, form not specified (detached or within the house); not listed in RR-1-3, RS-2, RS-3, TRD-1; adoption date not found; text read via search-engine rendering (Municode 403)"),
    ("attached_allowed", "unknown", "", "", KEN, "§3.04.A.4; §3.03.A one principal building per lot", L, "form of the RS-1 domestic-help quarters not specified; otherwise one principal building per lot"),
    ("occupant_restriction", "employee_only", "", "", KEN, "§3.04.A.4", L, "domestic help (household employees), not relatives"),
    ("owner_occupancy", "none", "", "", KEN, "§3.04.A.4", L, "none stated"),
    ("max_size_sqft", "accessory buildings: lesser of 15% of lot or 840, and <= house footprint", "2024-09-16", "", KEN, "§3.03.D.4.d (Ord. 36-24)", L, ""),
    ("parking_required", "unknown", "", "", KEN, "§6.01 not read", U, ""),
    ("approval_type", "permitted use (RS-1)", "", "", KEN, "§3.04.A.4", L, "listed as permitted, so a zoning/building permit"),
], note="Borderline: restricted because the code names a domestic-help dwelling (a second dwelling for household employees) in RS-1. Under the owner's ADU definition (2026-10-24: a dwelling unit with its own kitchen, sanitation and sleeping facilities for permanent habitation) it counts only if the quarters are a complete dwelling unit; the text read does not say so. prohibited_implicit if not. First pass: 'domestic-help quarters' is a lead term, not a dwelling-unit term, so ordinance_status is unmentioned.",
   flags=["related_occupant", "district_limited"])

RAC = "https://library.municode.com/wi/racine/codes/code_of_ordinances?nodeId=PTIIMUCO_CH114ZO_ARTVDIRE_DIV2REDI"
RAC_BZA = "https://cityofracine.legistar1.com/cityofracine/attachments/0f020bcb-d8cf-494e-8c4a-98cc8c625efb.pdf"
muni(["5510166000"], "Racine city", PEXP, "coded_verified", "2026-03-03",
     "One detached or attached ADU by right on every R1/R2 single-family lot; at least 600 sq ft; no extra parking; no owner-occupancy or relative rule.", [
    ("detached_allowed", "prohibited", "", "", RAC_BZA, "BZA staff report 1038-24 (2024-11-18): converting an accessory building to a dwelling unit needs a variance from §114-292; staff: ADUs only 'if the code allowed'", V, "official report re-read 2026-10-24 (pdftotext); code text §114-272, §114-691 read via search-engine rendering of Municode"),
    ("attached_allowed", "prohibited", "", "", RAC, "§114-272, §114-292", L, "Municode text via search-engine rendering; pending rewrite ZOrd.0007-26 (introduced 2026-09-11) also has no ADU use"),
])

APP_LEG = "https://cityofappleton.legistar.com/LegislationDetail.aspx?GUID=96A34E37-FF1B-4AE2-B7A9-1E1BF0F8367E&ID=4970068"
APP_GUIDE = "https://cms2.revize.com/revize/appletonwi/Documents/CommDev/Planning/Plans%20and%20Reports/City%20of%20Appleton%20-%20Accessory%20Dwelling%20Units%20(ADU)%20Guide.pdf"
APP_ACC = "https://cms2.revize.com/revize/appletonwi/Documents/CommDev/Building%20Inspection/Permits/building/Accessory%20Bldg%20.pdf"
muni(["5508702375", "5501502375", "5513902375"], "Appleton city", "scenario_benchmark", "coded_source_lead", "2026-02-01",
     "Guarantees at least 600 sq ft for an attached ADU regardless of house size and attached garage (lifts the 35%-of-house attached-accessory cap); otherwise already benchmark (ADU plus junior ADU by right, no parking, no owner occupancy).", [
    ("detached_allowed", "prohibited", "", "2021-07-12", APP_LEG, "before Ord. 25-21", L, "pre-2021 text not checked"),
    ("detached_allowed", "by_right", "2021-07-13", "", APP_LEG, "§23-55 (Ord. 25-21); §23-56 JADU (Ord. 26-21)", V, "R-1A, R-1B, R-1C, R-2, R-3"),
    ("attached_allowed", "by_right", "2021-07-13", "", APP_LEG, "§23-55, §23-56", V, ""),
    ("owner_occupancy", "none", "2021-07-13", "", APP_LEG, "§23-55", V, "cannot be sold separately (deed restriction)"),
    ("occupant_restriction", "none", "2021-07-13", "", APP_LEG, "§23-55", V, ""),
    ("max_size_sqft", "ADU+JADU <= principal GFA; JADU <= 500", "2021-07-13", "", APP_LEG, "§23-55, §23-56", V, ""),
    ("parking_required", "0", "2021-07-13", "", APP_LEG, "§23-55", V, ""),
    ("max_size_sqft", "attached accessory floor area (incl. attached garage): 35% of principal GFA incl. basement, max 1600 (Jan 2025 ADU guide) or the greater of 1600 and 35% (building-inspection worksheet)", "", "", APP_ACC, "§23-43(i) as summarized by the city (codified text not read)", L, "official summaries conflict: the ADU guide edited 2025-01-07 used 'x 0.35 or max 1,600' (can fall below 600 sq ft for a small house with an attached garage); the accessory-building worksheet says 'whichever is greater'; the guide re-issued 2026-10-14 no longer states the cap"),
    ("approval_type", "building permit", "2021-07-13", "", APP_LEG, "§23-55", V, "guide 2026-10-14: deed restriction, then building permits"),
], note="Owner decision G2-6 (2026-10-24): coded scenario_benchmark on the city's 2026-10-14 ADU guide, which no longer states the 35% attached-accessory cap; class basis is a source lead until §23-43(i) codified text is read. Earlier 2025 guide applied the cap to attached ADUs.",
   flags=[])

WK = "https://legistar2.granicus.com/waukesha/attachments/fb763278-f10c-4d54-91b2-240833e68012.pdf"
WK3 = "https://legistar2.granicus.com/waukesha/attachments/c852c290-1ccf-4801-9967-8d87347537fd.pdf"
WK6 = "https://legistar2.granicus.com/waukesha/attachments/8c8662e7-dfc1-4ece-b405-5a0c1116a477.pdf"
muni(["5513384250"], "Waukesha city", RESTR, "coded_verified", "2026-09-01",
     "Removes 1 required parking space per ADU; guarantees a 600 sq ft ADU regardless of house size (attached cap 40% of the house; detached 75%).", [
    ("detached_allowed", "prohibited", "", "2026-08-31", "https://www.zoneomics.com/code/waukesha-WI", "old Ch. 22, §22.24 RS-1", L, "no ADU or in-law provision in old code (mirror plus March 2026 news)"),
    ("detached_allowed", "by_right", "2026-09-01", "", WK3, "Ch. 22.03(5)(A) use table, RN-1 to RN-4 (Ord. 2026-4, adopted 2026-07-07)", V, ""),
    ("attached_allowed", "by_right", "2026-09-01", "", WK3, "22.03(6)(C)(4)", V, "attached, internal, basement or attic"),
    ("owner_occupancy", "none", "2026-09-01", "", WK3, "22.03(6)(C)(4)", V, "6-month owner rule in May 2025 draft was dropped"),
    ("occupant_restriction", "none", "2026-09-01", "", WK3, "22.03(6)(C)(4)", V, ""),
    ("max_size_sqft", "detached lesser of 1200 or 75% of principal; attached 40% of principal or whole basement/attic", "2026-09-01", "", WK3, "22.03(6)(C)(4)", V, "600 sq ft detached needs house >= 800 sq ft"),
    ("parking_required", "1", "2026-09-01", "", WK6, "Table 22.06(4)(B)(3)", V, ""),
    ("approval_type", "permitted use plus staff site plan and architectural review", "2026-09-01", "", WK, "22.11(4)(B)(2)", V, ""),
], flags=["extra_parking", "size_below_benchmark"])

EC = "https://www.eauclairewi.gov/DocumentCenter/View/1033/Land-Development-Ordinance-PDF"
EC7614 = "https://www.eauclairewi.gov/DocumentCenter/View/1479/No-7614-PDF"
muni(["5503522300", "5501722300"], "Eau Claire city", RESTR, "coded_verified", "2026-05-04",
     "Removes 1 required parking space per ADU; administrative limited-use permit becomes a plain zoning permit.", [
    ("detached_allowed", "by_right", "1990-01-01", "2025-09-30", "https://www.eauclairewi.gov/DocumentCenter/View/1036/Zoning-Ordinance-PDF", "old §18.30.040(A) (Ord. 5037, 1990; Ord. 6672, 2006)", V, "only for persons employed on the premises and immediate family; effective_from approximate (1990 ordinance)"),
    ("occupant_restriction", "related_only", "1990-01-01", "2025-09-30", "https://www.eauclairewi.gov/DocumentCenter/View/1036/Zoning-Ordinance-PDF", "old §18.30.040(A)", V, "employee/family only; effectively a ban"),
    ("detached_allowed", "by_right", "2025-10-01", "", EC, "LDO Table 17.03.04(A) ('L' limited use), 17.03.04(B)(2)", V, "NSR, GR, NR, MR, UR (column mapping inferred)"),
    ("attached_allowed", "by_right", "2025-10-01", "", EC, "17.03.04(B)(2)", V, ""),
    ("owner_occupancy", "none", "2025-10-01", "", EC, "LDO full text", V, "Feb 2024 draft 6-month rule dropped"),
    ("occupant_restriction", "none", "2025-10-01", "", EC, "17.03.04(B)(2)", V, ""),
    ("max_size_sqft", "detached lesser of 1500 or 20% of lot; attached 40% of building", "2025-10-01", "", EC, "Table 17.03.04(B)", V, ""),
    ("parking_required", "1", "2025-10-01", "", EC, "Table 17.08.05(C)", V, "one abutting on-street space may count"),
    ("approval_type", "administrative limited use permit (17.12.09)", "2025-10-01", "", EC, "17.03.01, 17.12.09", V, ""),
    ("other", "LDO amendment Ord. 7614 (adopted 2026-04-28, published 2026-05-04): no ADU, ADU-parking or limited-use change", "2026-05-04", "", EC7614, "Ord. 7614 §§1-67", L, "read via search-engine rendering (city site 403 to plain HTTP); changes child care, ACU entrances, contractor services, cottage courts, stormwater"),
], note="Two 2026 LDO amendments: Ord. 7614 (effective on publication 2026-05-04; listed by the city as 'effective April 28, 2026') was read via a rendering and does not touch ADUs; the amendment effective 2026-08-11 (Plan Commission 2026-08-03: three/four-unit locations, parking-lot islands, form-based standards, live-work and accessory commercial units) is a scanned PDF and was not read. rules_as_of stays 2026-05-04.",
   flags=["extra_parking", "size_below_benchmark"])

OSH = "https://web.archive.org/web/20251214231347/https://www.oshkoshwi.gov/WebLink/DocView.aspx?id=1183289&dbid=0&repo=Laserfiche"
muni(["5513960500"], "Oshkosh city", RESTR, "coded_verified", "2026-03-31",
     "Raises the 400 sq ft ADU cap so at least 600 sq ft is allowed.", [
    ("detached_allowed", "prohibited", "", "2023-02-27", OSH, "Ch. 30 before 2023 revision", L, "in-family suite inside a house was allowed"),
    ("detached_allowed", "by_right", "2023-02-28", "", OSH, "§30-86(X) [Revised 02.28.23]", V, "'P' in 6 of 20 districts; district mapping source lead"),
    ("attached_allowed", "by_right", "2023-02-28", "", OSH, "§30-22(178), §30-86(X)", V, ""),
    ("owner_occupancy", "none", "2023-02-28", "", OSH, "§30-86(X)", V, "none stated"),
    ("occupant_restriction", "none", "2023-02-28", "", OSH, "§30-86(X)", V, ""),
    ("max_size_sqft", "400", "2023-02-28", "", OSH, "§30-86(X)", V, ""),
    ("parking_required", "0", "2023-02-28", "", OSH, "§30-86(X)", V, "none stated"),
    ("approval_type", "permitted use ('P')", "2023-02-28", "", OSH, "§30-86(X)", V, ""),
], flags=["size_below_benchmark"])

JV = "https://library.municode.com/wi/janesville/codes/code_of_ordinances"
muni(["5510537825"], "Janesville city", PIMP, "coded_source_lead", "2026-04-27",
     "ADUs by right (detached and attached, at least 600 sq ft, no extra parking, no owner occupancy) in all single-family districts.", [
    ("detached_allowed", "prohibited", "", "", JV, "Ch. 42, §42-353 (one principal building per lot), §42-362, §42-440", L, "text read via search extracts; pending Ch. 46 draft (2026-04-30) would allow ADUs with owner occupancy, not adopted as of 2026-10-23"),
    ("attached_allowed", "prohibited", "", "", JV, "§42-440", L, "two-family by CUP in R1 on lots >= 10,000 sq ft is a duplex path, not an ADU"),
], note="Re-check council action on draft Ch. 46 before freezing at 2026-10-31.")

WA = "https://westalliswi.legistar1.com/westalliswi/attachments/df2ec2d7-5409-4759-a080-5366789281e4.pdf"
muni(["5507985300"], "West Allis city", RESTR, "coded_verified", "2026-02-24",
     "Guarantees a 600 sq ft ADU regardless of house size (removes 50%-of-principal footprint cap); allows attached/internal ADUs by right in RA-1/RA-2.", [
    ("detached_allowed", "prohibited", "", "2022-05-02", WA, "old Ch. 12 (repealed text quoted in O-2022-0024)", V, ""),
    ("detached_allowed", "by_right", "2022-05-03", "", WA, "Ch. 19 §19.36(1) (O-2022-0024)", V, "limited use, 1 per lot, all residential districts"),
    ("attached_allowed", "conditional", "2022-05-03", "", WA, "§19.16, §19.33", V, "internal/attached second unit = 2-unit dwelling; limited in RA-1/RA-2 to lots by commercial districts (interpretation)"),
    ("owner_occupancy", "none", "2022-05-03", "", WA, "Ch. 19", V, ""),
    ("occupant_restriction", "none", "2022-05-03", "", WA, "Ch. 19", V, ""),
    ("max_size_sqft", "footprint <= 50% of principal, max 800", "2023-06-06", "", "https://westalliswi.legistar1.com/westalliswi/attachments/c1e7f426-a56f-412e-bac2-b38e83565261.pdf", "O-2023-0031", V, "700 sq ft cap 2022-05-03 to 2023-06-05"),
    ("parking_required", "0", "2023-06-06", "", "https://westalliswi.legistar1.com/westalliswi/attachments/c1e7f426-a56f-412e-bac2-b38e83565261.pdf", "§19.44 (maximums only)", V, ""),
    ("approval_type", "design review permit plus building permit", "2022-05-03", "", WA, "§19.36", V, "detached; attached/internal second units follow two-unit rules (conditional where allowed)"),
], flags=["size_below_benchmark", "form_limited"])

LAX = "https://legistar.granicus.com/CityofLaCrosse/attachments/239dbc28-943b-4645-9f22-e87475d777da.docx"
muni(["5506340775"], "La Crosse city", RESTR, "coded_verified", "2024-02-17",
     "Attached/internal ADUs by right; removes ongoing owner-occupancy rule and deed restriction.", [
    ("detached_allowed", "prohibited", "", "2024-02-16", LAX, "§115-390(1)(d)(3) plumbing ban in accessory structures (amended by Ord. 5280)", V, ""),
    ("detached_allowed", "by_right", "2024-02-17", "", LAX, "§115-405 (Ord. 5280, Legistar 23-1243, published 2024-02-17)", V, "R-1 to R-4, Washburn Residential"),
    ("attached_allowed", "prohibited", "2024-02-17", "", LAX, "§115-405", V, "freestanding, converted garage or garage addition only"),
    ("owner_occupancy", "ongoing", "2024-02-17", "", LAX, "§115-405", V, "deed restriction before permit"),
    ("occupant_restriction", "none", "2024-02-17", "", LAX, "§115-405", V, ""),
    ("max_size_sqft", "lesser of 900 or house floor area", "2024-02-17", "", LAX, "§115-405", V, ""),
    ("parking_required", "0", "2024-02-17", "", LAX, "§115-405", V, ""),
    ("approval_type", "building permit (permitted accessory use)", "2024-02-17", "", LAX, "§115-405", V, ""),
], flags=["form_limited", "owner_occupancy"])

SHEB_CC19 = "https://mccmeetings.blob.core.usgovcloudapi.net/sheboygnwi-pubu/MEET-Packet-e1d3cb4ec4c5400797b865c76fb7f273.pdf"
SHEB_CC24 = "https://mccmeetings.blob.core.usgovcloudapi.net/sheboygnwi-pubu/MEET-Minutes-d7d70b7e4efe4892ad3bfe1f6a029d4b.pdf"
SHEB_CC25 = "https://mccmeetings.blob.core.usgovcloudapi.net/sheboygnwi-pubu/MEET-Minutes-aa9ca83a5a024e488fdf0bbbd0b74044.pdf"
SHEB = "https://mccmeetingspublic.blob.core.usgovcloudapi.net/sheboygnwi-meet-1ab88e5a89ad4af6836be2c56109cdb0/ITEM-Attachment-001-015d62d52b424fc985217ee1b0ae1f13.pdf"
muni(["5511772975"], "Sheboygan city", PEXP, "coded_verified", "2026-04-08",
     "Detached and attached ADUs by right where none are allowed.", [
    ("detached_allowed", "prohibited", "2020-02-07", "", SHEB, "Ch. 105, §105-722 (accessory use never a residence), §105-202", V, "Ch. 105 as compiled 2023-04-27 (council-packet copy); no later ADU amendment adopted, see the 'other' rows"),
    ("attached_allowed", "prohibited", "2020-02-07", "", SHEB, "§105-7 (no split except two-flat)", V, ""),
    ("other", "Gen. Ord. 37-25-26 (zoning rewrite with ADUs) laid over 2026-01-05, then filed 2026-03-16", "", "", SHEB_CC24, "Common Council minutes 2026-03-16, items 30-31; agenda 2026-01-05 item 12", V, "agenda 2026-01-05: " + SHEB_CC19),
    ("other", "Gen. Ord. 39-25-26 (revised rewrite: ADUs with 183-day owner occupancy, one-family occupancy, 40% size cap) referred to the 2026-27 council/Committee of the Whole on 2026-04-08; not adopted", "", "", SHEB_CC25, "Common Council minutes 2026-04-08, item 12", V, "news 2026-10-20 (Seehafer News) still describes a proposed rewrite with community sessions; source lead for status after April"),
], note="Gate 1 listed Sheboygan as a December 2025 liberalizer; the ordinance was laid over and filed, and its successor referred to the new council, never adopted. Re-check before the freeze.")

TOSA = "https://wauwatosacitywi.legistar1.com/wauwatosacitywi/attachments/f54c270b-576f-4e05-a954-36755d2e4f9c.pdf"
muni(["5507984675"], "Wauwatosa city", BENCH, "coded_verified", "2025-11-18",
     "None beyond current code on most parcels. Edge cases only: houses under 600 sq ft (cap = house size), and replacement parking: the principal house's 1 required space must be maintained or replaced on-site (§24.10.075(B)(7)), which the reform's no-additional-parking rule would remove for garage conversions.", [
    ("detached_allowed", "by_right", "2019-06-18", "", "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/16684/962746/pdf?forceDownload=true", "§24.10.075 (O-19-11)", V, ""),
    ("attached_allowed", "by_right", "2019-06-18", "", "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/16684/962746/pdf?forceDownload=true", "§24.10.075 (O-19-11)", V, ""),
    ("max_size_sqft", "lesser of 650 or 49% of house", "2019-06-18", "2022-09-19", "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/16684/962746/pdf?forceDownload=true", "O-19-11", V, ""),
    ("max_size_sqft", "lesser of 900 or house GFA", "2022-09-20", "2025-11-17", "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/wauwatosa/ordinances/documents/1714691803_O-22-24.pdf", "O-22-24", V, ""),
    ("max_size_sqft", "lesser of 1000 or house GFA", "2025-11-18", "", TOSA, "§24.10.075 recreated by O-25-25", V, "effective on publication; publication date not found"),
    ("owner_occupancy", "none", "2019-06-18", "", TOSA, "§24.10.075", V, ""),
    ("occupant_restriction", "none", "2019-06-18", "", TOSA, "§24.10.075", V, ""),
    ("parking_required", "0", "2019-06-18", "", TOSA, "§24.10.075(B)(7) (O-25-25 Part XXII); §24.11.020 (Part XXIV)", V, "re-read 2026-10-24 (O-25-25 sha256 ccbc6617...6c55c66): 'No additional parking is required for an accessory dwelling unit. Existing required parking for the principal dwelling unit must be maintained or replaced on-site'; a detached house needs 1.0 space per dwelling unit, so a garage conversion that removes it needs a replacement space (the same edge case as Madison)"),
    ("approval_type", "building permit", "2019-06-18", "", TOSA, "§24.10.075", V, ""),
    ("other", "ADUs allowed on any lot occupied by a detached house, semi-detached house, attached house or two-unit house (no district list); one per lot", "2025-11-18", "", TOSA, "§24.10.075(B)(2),(3) (O-25-25 Part XXII)", V, "no unlisted residential district found; R-district table refers ADU standards to §24.10.075"),
], note="Benchmark kept by owner decision 2026-10-24. Edge case: §24.10.075(B)(7) requires the principal house's existing required parking (1 space) to be maintained or replaced on-site, which the benchmark's no-additional-parking rule would remove for garage conversions. No district limit: ADUs are allowed wherever a house occupies the lot.")

FDL = "https://www.fdl.wi.gov/"
muni(["5503926275"], "Fond du Lac city", RESTR, "coded_source_lead", "2026-03-25",
     "Removes ongoing owner-occupancy rule; removes 1 extra parking space; lifts footprint cap for small houses.", [
    ("detached_allowed", "prohibited", "", "2025-02-25", FDL, "Ch. 720 Schedule II before Ord. 3809 (no ADU row); City Council minutes 2025-02-26", V, ""),
    ("detached_allowed", "by_right", "2025-02-26", "", FDL, "§720-11C(29), Schedule II ('SC' in R-1 to R-4) (Ord. 3809)", L, "permitted with special conditions"),
    ("attached_allowed", "by_right", "2025-02-26", "", FDL, "§720-11C(29)", L, ""),
    ("owner_occupancy", "ongoing", "2025-02-26", "", FDL, "§720-11C(29)", L, ""),
    ("occupant_restriction", "none", "2025-02-26", "", FDL, "§720-11C(29)", L, "rentals >= 30 days"),
    ("max_size_sqft", "detached lesser of 800 or house footprint; attached greater of 800 or 50% of footprint; <= 2 bedrooms", "2025-02-26", "", FDL, "§720-11C(29)", L, ""),
    ("parking_required", "1", "2025-02-26", "", FDL, "§720-11C(29)", L, ""),
    ("approval_type", "administrative (special conditions)", "2025-02-26", "", FDL, "Art. VI not read", L, ""),
], note="§720-11C(29) text read through the Zoneomics mirror (ecode360 403); adoption of Ord. 3809 from council minutes 2025-02-26.",
   flags=["owner_occupancy", "extra_parking"])

NB = "https://www.zoneomics.com/code/new-berlin-WI/chapter_5"
muni(["5513356375"], "New Berlin city", RESTR, "coded_source_lead", "2026-01-27",
     "Detached and semi-detached ADUs; at least 600 sq ft (50%-of-house cap); ADUs outside agricultural/single-family districts; removes owner-occupancy, related-occupant and 2-occupant rules; no extra parking.", [
    ("detached_allowed", "prohibited", "2013-06-17", "", NB, "§275-42 C(3); §275-42 B(1)(a)[2][b][iii]", L, "confirmed by City Sheds guidance PDF (verified)"),
    ("attached_allowed", "by_right", "2013-06-17", "", NB, "§275-42 C(3) family dwelling unit, zoning permit §275-24", L, "agricultural and single-family districts only"),
    ("owner_occupancy", "ongoing", "2013-06-17", "", NB, "§275-42 C(3)", L, ""),
    ("occupant_restriction", "related_only", "2013-06-17", "", NB, "§275-42 C(3)", L, "max 2 occupants; deed restriction"),
    ("max_size_sqft", "50% of principal living area", "2013-06-17", "", NB, "§275-42 C(3)", L, ""),
    ("parking_required", "unknown", "", "", NB, "Table 275-57-1", U, ""),
    ("approval_type", "administrative zoning permit", "2013-06-17", "", NB, "§275-24", L, ""),
], note="Coded at Gate 1 (POLICY_EVIDENCE_MAP section 3); Municode blocked; code version through Ord. 2717 (2026-01-27).",
   flags=["form_limited", "owner_occupancy", "related_occupant", "size_below_benchmark"])

WAU = "https://library.municode.com/wi/wausau/codes/code_of_ordinances?nodeId=TIT23ZO_ARTIIILAUSRE"
muni(["5507384475"], "Wausau city", RESTR, "coded_verified", "2026-07-14",
     "Detached and attached ADUs by right (not conditional use) in all single-family districts incl. DR-6; removes owner-occupancy; at least 600 sq ft always allowed (800 sq ft / 75% cap).", [
    ("detached_allowed", "conditional", "2020-01-01", "", WAU, "§23.03.05 use table; §23.03.28(6)", V, "RH-35, SR-2, SR-3, SR-5, SR-7, TF-10, TRD-12; Title 23 adopted 2020 (date approximate, source lead)"),
    ("attached_allowed", "conditional", "2020-01-01", "", WAU, "§23.03.28(6)", V, "in-family suite §23.03.28(7) by right but family only, internal connection"),
    ("owner_occupancy", "ongoing", "2020-01-01", "", WAU, "§23.03.28(6)(e)1", V, ""),
    ("occupant_restriction", "none", "2020-01-01", "", WAU, "§23.03.28(6)", V, ""),
    ("max_size_sqft", "lesser of 800 or 75% of house", "2020-01-01", "", WAU, "§23.03.28(6)", V, ""),
    ("parking_required", "unknown", "", "", WAU, "§23.03.28(6) silent; house needs 2", U, ""),
    ("approval_type", "conditional use permit", "2020-01-01", "", WAU, "§23.03.05", V, ""),
], note="Pre-2020 rules not found.", flags=["discretionary_review", "owner_occupancy", "district_limited", "size_below_benchmark"])

BF = "https://www.codepublishing.com/WI/Brookfield/html/Brookfield17/Brookfield1728.html"
muni(["5513310025"], "Brookfield city", PIMP, "coded_verified", "2026-02-17",
     "One ADU (separate dwelling with kitchen) per single-family parcel, detached and attached, by right in R-1 to R-3; at least 600 sq ft; no extra parking; no owner-occupancy or related-occupant rule.", [
    ("detached_allowed", "prohibited", "", "", BF, "§17.04.020 (one-family dwelling), §17.28.010(F)(6)", V, "separate guest houses only on lots > 3 acres with Plan Commission review; 'guest house' undefined"),
    ("attached_allowed", "prohibited", "", "", BF, "§17.28.010(F)(6)", V, "guest houses physically incorporated into the house are allowed but are guest space, not a second unit"),
    ("other", "servants' quarters (occupied only by servants employed on the premises, not rented) are a permitted accessory use in the UC Upland Conservancy district only, not in R-1 to R-3", "", "", "https://www.codepublishing.com/WI/Brookfield/html/Brookfield17/Brookfield1724.html", "Ch. 17.24 UC district permitted accessory uses", V, "found by the 2026-10-24 rescan with the expanded term list"),
], note="Guest houses (undefined; guest space, not permanent habitation) and the UC-only servants' quarters are not ADUs under the owner's definition (2026-10-24: a dwelling unit with its own kitchen, sanitation and sleeping facilities for permanent habitation), so prohibited_implicit is no longer borderline on that ground. Mayor re-elected 2026-04-07 opposing ADUs (source lead).")

BEL = "https://www.zoneomics.com/code/beloit-WI"
muni(["5510506500"], "Beloit city", RESTR, "coded_source_lead", "2026-06-01",
     "Rentable ADUs by right on every single-family parcel, detached and attached; removes guest/employee no-rent limit and 12,000 sq ft lot minimum; exempts ADUs from the 1,000 sq ft minimum dwelling size and the single-to-multi conversion ban.", [
    ("detached_allowed", "by_right", "2001-01-01", "", BEL, "Ch. 19 §6.3.3(a) private guest houses / detached employee quarters", L, "lots >= 12,000 sq ft and 85 ft wide; Ord. 2946 (2001), date approximate"),
    ("attached_allowed", "prohibited", "2025-06-02", "", BEL, "§6.2.11(b)(8) (Ord. 3868) conversion ban except PUD", L, ""),
    ("occupant_restriction", "other", "2001-01-01", "", BEL, "§11.3.101 guest house not rented", L, "non-paying guests or employees; no rental"),
    ("min_lot_size", "12000", "2001-01-01", "", BEL, "§6.3.3(a)", L, ""),
    ("max_size_sqft", "accessory buildings greater of 720 or 10% of lot, <= 1200 each", "2016-04-27", "", BEL, "§6.3.4(d) (Ord. 3574)", L, ""),
    ("approval_type", "permitted accessory use", "2001-01-01", "", BEL, "§6.3.3(a)", L, ""),
], note="Borderline: prohibited_implicit if non-rented guest houses and employee quarters are not counted as an ADU form. Under the owner's ADU definition (2026-10-24: own kitchen, sanitation and sleeping facilities for permanent habitation) guest houses for non-paying guests are not permanent habitation; employee quarters count only if they are complete dwelling units, which the text read does not say. First pass: both are lead terms, so ordinance_status is unmentioned.",
   flags=["related_occupant", "form_limited", "lot_minimum", "other"])

GF = "https://library.municode.com/wi/greenfield/codes/code_of_ordinances?nodeId=CH21ZOCO_PT4ZODIDIESDIUSRE_DIV21.04.0800ACTEUSSTRE_21.04.0802DESTACUSREDI"
muni(["5507931175"], "Greenfield city", PIMP, "coded_source_lead", "2026-10-23",
     "One ADU per single-family parcel, detached and attached, by right in R-1 to R-4B; at least 600 sq ft; no extra parking; no owner-occupancy or related-occupant rule.", [
    ("detached_allowed", "prohibited", "", "", GF, "§21.03.0206 one principal building; Table 21.04.0602; §21.03.0210", L, "Municode via search-engine rendering; §§21.03.0206/0210 via mirror"),
    ("attached_allowed", "prohibited", "", "", GF, "Table 21.04.0602 (two-family only in R-4, R-4A, R-4B, MFR, PUD)", L, "Municode via search-engine rendering"),
], note="Municode currency date not shown; rules_as_of is the access date.")

FR = "https://www.franklinwi.gov/Files/Planning/UDO-Rewrite-2025/2025-UDO-Rewrite-Text.pdf"
muni(["5507927300"], "Franklin city", RESTR, "coded_verified", "2025-06-09",
     "Detached and attached ADUs by right in all residential districts (currently conditional use); removes owner primary-residence requirement.", [
    ("detached_allowed", "prohibited", "1998-01-01", "2025-06-08", "https://franklinwi.gov/Files/Planning/UDOTextAmendmentOrd/UDO_UpdatedVersion_Dec192014.pdf", "Ord. 98-1493 UDO (one principal building except R-1E)", V, "R-1E allowed guest/servant/caretaker quarters; effective_from approximate"),
    ("detached_allowed", "conditional", "2025-06-09", "", FR, "Table 15-3-04(B) (Ord. 2025-2675)", V, "all five residential districts"),
    ("attached_allowed", "conditional", "2025-06-09", "", FR, "Table 15-3-04(B); internal ADU 'P' by right", V, ""),
    ("owner_occupancy", "ongoing", "2025-06-09", "", FR, "§15-4-13(A)(12), (B)(4)", V, ""),
    ("occupant_restriction", "none", "2025-06-09", "", FR, "§15-4-13", V, ""),
    ("max_size_sqft", "greater of 25% of house or 1200", "2025-06-09", "", FR, "§15-4-13(A)(5), (B)(2)", V, ""),
    ("parking_required", "0", "2025-06-09", "", FR, "§15-5-01(A)(1) maximums only", V, ""),
    ("approval_type", "conditional use permit (internal: permit)", "2025-06-09", "", FR, "Table 15-3-04(B)", V, ""),
], flags=["discretionary_review", "owner_occupancy"])

OC = "https://assets.parkingreform.org/assets/7d1088f1-4f0b-4f6a-a368-d7a3b6c4d398/oak-creek-wisconsin-united-states-attachment.pdf"
muni(["5507958800"], "Oak Creek city", RESTR, "coded_verified", "2026-04-06",
     "ADUs by right (currently conditional use) in all single-family districts incl. ER/Rs-5/Rd-1; standalone detached ADUs (currently only above/within an existing garage); removes owner-occupancy; at least 600 sq ft always allowed; removes extra ADU parking.", [
    ("detached_allowed", "conditional", "2022-03-15", "", OC, "§17.0414(b)(4) (only above or within an existing detached garage)", V, "Rs-1 to Rs-4 only (Table 17.0304(b))"),
    ("attached_allowed", "conditional", "2022-03-15", "", OC, "§17.0414", V, ""),
    ("owner_occupancy", "ongoing", "2022-03-15", "", OC, "§17.0414(b)(1)", V, ""),
    ("occupant_restriction", "none", "2022-03-15", "", OC, "§17.0414", V, ""),
    ("max_size_sqft", "lesser of 800 or 50% of house", "2022-03-15", "", OC, "§17.0414(b)(2)", V, ""),
    ("parking_required", "1", "2022-03-15", "", OC, "§17.0414(b)(7) (in addition to principal; at least 1)", V, ""),
    ("approval_type", "conditional use permit", "2022-03-15", "", OC, "§17.0804(e)", V, ""),
], note="Pre-2022 rules not found; ordinance number of the 2022 rewrite not found.",
   flags=["discretionary_review", "owner_occupancy", "form_limited", "district_limited", "size_below_benchmark", "extra_parking"])

MAN = "https://www.codepublishing.com/WI/Manitowoc/html/Manitowoc15/Manitowoc15110.html"
muni(["5507148500"], "Manitowoc city", PIMP, "coded_verified", "2026-09-30",
     "Detached and attached ADUs by right where none are allowed.", [
    ("detached_allowed", "prohibited", "", "", MAN, "Ch. 15 (no ADU text; R-2/R-3 single-family)", V, "2023 ADU draft PC 19-2023: no action; Ch. 35 discussion draft (2026-08-14) not adopted"),
    ("attached_allowed", "prohibited", "", "", MAN, "Ch. 15", V, ""),
    ("other", "secondary dwelling units (within the house, freestanding or above a garage, <= 800 sq ft) allowed only inside a Traditional Neighborhood Development approved under §15.730", "", "", "https://www.codepublishing.com/WI/Manitowoc/html/Manitowoc15/Manitowoc15730.html", "§15.730 (TND) definitions and design standards", V, "found by the 2026-10-24 rescan; not available on existing R-2/R-3 lots"),
], note="Borderline: secondary dwelling units exist only within a TND, a whole-neighborhood plan an existing homeowner cannot use; counted as prohibited_implicit for ordinary single-family districts.")

WB = "https://cms9files.revize.com/westbend/17%20Chapter%20Municipal%20Code-%201.pdf"
muni(["5513185350"], "West Bend city", PIMP, "coded_source_lead", "2022-02-16",
     "One ADU per single-family parcel, detached and attached, by right, at least 600 sq ft, no extra parking, no owner/related rule (overrides one-principal-structure rule and 720 sq ft accessory cap).", [
    ("detached_allowed", "prohibited", "", "", WB, "Ch. 17 §17.09(6)(b), §17.15(1), §17.44(57)", V, "codified text dated 2022-02-16; 2022-2026 amendments not read (site 403)"),
    ("attached_allowed", "prohibited", "", "", WB, "§17.44(57) one family", V, ""),
])

SP = "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/13968/1423544/pdf"
SP922 = "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/13968/1245783/pdf?forceDownload=true"
SP896 = "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/13968/1162266/pdf"
SP_TBL = "https://library.municode.com/wi/sun_prairie/codes/code_of_ordinances?nodeId=TIT17ZO_CH17.16LAUSRE_17.16.030TALAUS"
muni(["5502578600"], "Sun Prairie city", RESTR, "coded_verified", "2026-05-08",
     "Extends ADUs to single-family parcels in the RH-35ac, CR-5ac and ER-1 districts (now excluded); approval is already ministerial (special use reviewed by staff, no hearing) and needs no extra parking.", [
    ("detached_allowed", "prohibited", "", "2026-05-07", SP, "§17.16.140 before Ord. 984 (accessory buildings never a residence)", V, "whether ADUs were allowed before an earlier code is not verified"),
    ("attached_allowed", "prohibited", "", "2026-05-07", SP, "§17.16.140 before Ord. 984", V, ""),
    ("detached_allowed", "by_right", "2026-05-08", "", SP, "§17.16.140(33)(b) special use regulations (Ord. 984, adopted 2026-05-05, published 2026-05-08); (a) permitted by right and (c) conditional use: 'Not applicable'", V, "by right with standards: a special use is approved by the zoning administrator after staff review, no hearing (§17.44.040); SR-4, MR-8, UR-12, NC, UC, CC, PD; re-read 2026-10-24"),
    ("attached_allowed", "by_right", "2026-05-08", "", SP, "§17.16.140(33)(b)", V, "same districts; one attached or two detached ADUs per lot"),
    ("other", "single-family districts excluded: RH-35ac (Rural Holding), CR-5ac (Countryside Residential), ER-1 (Estate Residential); single-family detached is permitted in all six residential districts", "", "", SP896, "Table 17.16.030 district columns (Ord. 896, 2022); dwelling-type rows via Municode rendering", V, "district list from the official ordinance table; the single-family rows of Table 17.16.030 were read via a search-engine rendering of Municode"),
    ("owner_occupancy", "none", "2026-05-08", "", SP, "§17.16.140(33)", V, ""),
    ("occupant_restriction", "none", "2026-05-08", "", SP, "§17.16.140(33)", V, ""),
    ("max_size_sqft", "1000 (attached; detached footprint)", "2026-05-08", "", SP, "§17.16.140(33)", V, "one attached or two detached"),
    ("parking_required", "0", "2026-05-08", "", SP, "§17.16.140(33)", V, ""),
    ("approval_type", "special use, ministerial: staff review and zoning administrator approval, no hearing", "2026-05-08", "", SP922, "§17.44.040(B),(D) as amended by Ord. 922 (2023-09-19); §17.16.020(C)", V, "if a special-use standard cannot be met, the applicant may seek a conditional use (Plan Commission and Council)"),
], flags=["district_limited"])

SUP = "https://library.municode.com/wi/superior/codes/code_of_ordinances?nodeId=PTIICOOR_CH122ZO"
muni(["5503178650"], "Superior city", PIMP, "coded_verified", "2025-12-02",
     "Detached and attached ADUs by right on single-family parcels where none are allowed.", [
    ("detached_allowed", "prohibited", "", "", SUP, "Ch. 122 Arts. I, IV, VI (no ADU provision)", V, "pending SRF zoning rewrite draft (Dec 2025) adds accessory dwellings; not adopted"),
    ("attached_allowed", "prohibited", "", "", SUP, "Ch. 122", V, ""),
])

STP = "https://www.stevenspoint.com/DocumentCenter/View/769/Chapter-23---Zoning--Floodplain"
muni(["5509777200"], "Stevens Point city", RESTR, "coded_verified", "2026-05-05",
     "ADUs by right (not conditional use); allows attached/internal ADUs; removes owner-occupancy; removes 1 parking space; removes the single-family-minimum / 10,000 sq ft R-3 lot requirement.", [
    ("detached_allowed", "conditional", "", "", STP, "§23.01(15)(b)", V, "R-LD, R-1 to R-5; adoption ~2022 (source lead), ordinance number not found"),
    ("attached_allowed", "prohibited", "", "", STP, "§23.01(15) (ADU defined as detached)", V, ""),
    ("owner_occupancy", "ongoing", "", "", STP, "§23.01(15)(g)", V, ">= 10 months/yr, recorded agreement"),
    ("occupant_restriction", "none", "", "", STP, "§23.01(15)", V, ""),
    ("min_lot_size", "district single-family minimum; 10000 in R-3", "", "", STP, "§23.01(15)", V, ""),
    ("max_size_sqft", "unknown (Ch. 30 detached accessory limit)", "", "", STP, "§23.01(15)", U, ""),
    ("parking_required", "1", "", "", STP, "§23.01(17)(c)(3)", V, ""),
    ("approval_type", "conditional use permit", "", "", STP, "§23.01(15)(b)", V, ""),
], flags=["discretionary_review", "form_limited", "owner_occupancy", "extra_parking", "lot_minimum"])

NEE = "https://www2.ci.neenah.wi.us/committees.nsf/0/740d7c8b6bbec18886258c6f005576e1/$FILE/A%2020250429PC.pdf"
muni(["5513955750"], "Neenah city", PEXP, "coded_source_lead", "2025-09-03",
     "Detached and attached ADUs by right where none are allowed.", [
    ("detached_allowed", "prohibited", "2014-08-06", "", NEE, "Ch. 26 §26-148 R-1 one single-family dwelling (Ord. 2014-14); §21-19 accessory building not a dwelling (Ord. 2023-07)", V, "PC minutes 2025: ADUs 'currently prohibited'; current text via mirror; no adoption found in 2026 PC/CC packets"),
    ("attached_allowed", "prohibited", "2014-08-06", "", NEE, "§26-148", V, ""),
], note="'Never adopted through Oct 2026' rests on absence in packets read; minutes search requires login.")

FIT = "https://fitchburgwi.gov/DocumentCenter/View/29094/2025-O-17"
muni(["5502525950"], "Fitchburg city", RESTR, "coded_verified", "2025-09-10",
     "Guarantees 600 sq ft where the 75%-of-house cap binds (houses under 800 sq ft) and confirms no parking minimum; otherwise already benchmark.", [
    ("attached_allowed", "conditional", "", "2025-09-09", "https://library.municode.com/wi/fitchburg/codes/code_of_ordinances?nodeId=TIIILAUSDE_CH22ZO_ARTIIREDI", "R-L, R-LM dependency living arrangements", V, "<= 750 sq ft, owner-occupied, caregiver/dependent occupant, interior door"),
    ("owner_occupancy", "ongoing", "", "2025-09-09", "https://library.municode.com/wi/fitchburg/codes/code_of_ordinances?nodeId=TIIILAUSDE_CH22ZO_ARTIIREDI", "dependency living arrangements", V, ""),
    ("detached_allowed", "by_right", "2025-09-10", "", FIT, "Sec. 22-230 (Ord. 2025-O-17, adopted 2025-09-09)", V, "effective day after publication (date approximate)"),
    ("attached_allowed", "by_right", "2025-09-10", "", FIT, "Sec. 22-230", V, ""),
    ("owner_occupancy", "none", "2025-09-10", "", FIT, "Sec. 22-230", V, "cannot be sold separately"),
    ("occupant_restriction", "none", "2025-09-10", "", FIT, "Sec. 22-230", V, ""),
    ("max_size_sqft", "75% of house floor area", "2025-09-10", "", FIT, "Sec. 22-230", V, ""),
    ("parking_required", "unknown", "", "", FIT, "Sec. 22-230 silent; Sec. 22-609", U, "leaning none"),
], note="Near-benchmark: the only flag is the 75%-of-house cap, which binds on houses under 800 sq ft; parking unknown (leaning none).",
   flags=["size_below_benchmark"])

MUS = "https://ecode360.com/29722805"
muni(["5513355275"], "Muskego city", RESTR, "coded_source_lead", "2026-03-24",
     "Detached ADUs by right (currently conditional, employee/relative only, no rental, 1,200 sq ft minimum); attached/internal ADUs by right without Plan Commission review; removes related-occupant and no-rental restrictions.", [
    ("attached_allowed", "conditional", "2009-05-12", "", MUS, "§400-165 mother-in-law/family unit (Plan Commission plan review)", L, "read via search rendering of ecode360"),
    ("detached_allowed", "conditional", "2009-05-12", "", MUS, "§400-172(A),(B)", L, "employee/relative quarters or guesthouse, >= 1,200 sq ft, no rental"),
    ("occupant_restriction", "related_only", "2009-05-12", "", MUS, "§400-165(C)", L, ""),
    ("owner_occupancy", "unknown", "", "", MUS, "§400-165", U, "no explicit rule"),
    ("max_size_sqft", "800 (internal unit)", "2009-05-12", "", MUS, "§400-165", L, ""),
    ("approval_type", "Plan Commission plan review / conditional use", "2009-05-12", "", MUS, "§400-165, §400-172", L, ""),
], note="ecode360 text read only via search-engine rendering (403).", flags=["discretionary_review", "related_occupant", "other"])

MEQ = "https://library.municode.com/wi/mequon/codes/code_of_ordinances?nodeId=PTIICOOR_CH58PLDERE_ARTIVZO_DIV3REDI_SDIIUSRE"
muni(["5508951150"], "Mequon city", RESTR, "coded_source_lead", "2025-12-09",
     "Detached ADUs; attached ADUs by right instead of conditional use in all single-family districts incl. R-5; removes ongoing owner-occupancy and family/caretaker-only occupancy; at least 600 sq ft (40% cap); confirms no extra parking.", [
    ("detached_allowed", "prohibited", "2021-06-08", "", MEQ, "§58-248(e)(1), §58-415", L, "guesthouse CUP (no kitchen, no rental) is not an ADU"),
    ("attached_allowed", "conditional", "2021-06-08", "", MEQ, "§58-248 (Ord. 2021-1591)", L, "R-1 to R-4 only"),
    ("owner_occupancy", "ongoing", "2021-06-08", "", MEQ, "§58-248(e)(2)", L, ""),
    ("occupant_restriction", "related_only", "2021-06-08", "", MEQ, "§58-248(e)(3)", L, "family, dependent, caretaker"),
    ("max_size_sqft", "40% of house living area", "2021-06-08", "", MEQ, "§58-248(e)(5)", L, ""),
    ("parking_required", "unknown", "", "", MEQ, "§58-441", U, ""),
    ("approval_type", "conditional use (basement units administrative with covenant)", "2021-06-08", "", MEQ, "§58-248(e)(9)", L, ""),
], note="Municode text read via search-engine rendering (403).",
   flags=["form_limited", "discretionary_review", "owner_occupancy", "related_occupant", "size_below_benchmark", "district_limited"])

DP = "https://www.deperewi.gov/egov/documents/1703171468_81245.pdf"
muni(["5500919775"], "De Pere city", RESTR, "coded_verified", "2026-07-21",
     "Removes ongoing owner-occupancy/deed-restriction rule; lifts the 30%-of-house cap on internal suites.", [
    ("detached_allowed", "by_right", "2023-01-01", "", DP, "Ch. 14 §14-27 backyard cottage", V, "R1, R2, RM-1, RM-2; pre-2023 status not determined"),
    ("attached_allowed", "by_right", "2023-01-01", "", DP, "§14-78(13) secondary suite", V, "cottage or suite, not both"),
    ("owner_occupancy", "ongoing", "2023-01-01", "", DP, "§14-27, §14-78(13)", V, "deed restriction"),
    ("occupant_restriction", "none", "2023-01-01", "", DP, "§14-27", V, ""),
    ("max_size_sqft", "cottage 650 footprint; suite 30% of principal GFA", "2023-01-01", "", DP, "§14-27, §14-78(13)", V, ""),
    ("parking_required", "0", "2023-01-01", "", DP, "§14-27", V, ""),
    ("approval_type", "permit", "2023-01-01", "", DP, "§14-27", V, ""),
], flags=["owner_occupancy", "size_below_benchmark"])

MTP = "https://ecode360.com/36325067"
muni(["5510154875"], "Mount Pleasant village", RESTR, "coded_source_lead", "2026-10-23",
     "Guarantees at least 600 sq ft regardless of house size (replaces 40% cap); removes the suite one-rental-unit rule; confirms no extra parking for cottages.", [
    ("detached_allowed", "by_right", "2020-06-08", "", MTP, "§90-110.20(g) backyard cottage; Table 90-310-1", L, "Ord. 19-2020 code rewrite; ADU origin date source lead; restated Ord. 09-2025"),
    ("attached_allowed", "by_right", "2020-06-08", "", "https://ecode360.com/36325586", "§90-330.110 secondary suite", L, ""),
    ("owner_occupancy", "ongoing", "2020-06-08", "", "https://ecode360.com/36325586", "§90-330.110(l) only one unit may be rented", L, "de facto; cottages need deed restriction"),
    ("occupant_restriction", "none", "2020-06-08", "", MTP, "§90-110.20(g)", L, "combined one-household cap"),
    ("max_size_sqft", "40% of principal GFA", "2020-06-08", "", MTP, "§90-110.20(g), §90-330.110", L, ""),
    ("parking_required", "0 (suite); unknown (cottage)", "2020-06-08", "", "https://ecode360.com/36325586", "§90-330.110", L, ""),
    ("approval_type", "zoning/building permit", "2020-06-08", "", MTP, "§90-110.20(g)", L, ""),
], note="ecode360 text read via search-engine rendering (403). Owner occupancy is coded ongoing because only one of the two units may be rented (de facto owner occupancy) and cottages need a deed restriction.",
   flags=["owner_occupancy", "size_below_benchmark"])

CAL = "https://data.zoninghub.com/viewfile.aspx?fileid=110664"
muni(["5510111950"], "Caledonia village", PIMP, "coded_verified", "2026-09-28",
     "Detached and attached ADUs by right on single-family lots (none now; a pending draft would be conditional use only).", [
    ("detached_allowed", "prohibited", "", "", CAL, "Plan Commission staff report 2026-09-28 (application 041-2026); Title 16 §16-6-3 to 16-6-7", V, "district text source lead (cached PDF)"),
    ("attached_allowed", "prohibited", "", "", CAL, "staff report 2026-09-28", V, "staff directed to draft conditional-use ADUs"),
])

PP = "https://ecode360.com/36640696"
muni(["5505963300"], "Pleasant Prairie village", PEXP, "coded_verified", "2026-08-24",
     "Detached and attached ADUs by right in all single-family districts (R-1 to R-6, R-4.5, A-2); repeals the §420-30B dwelling ban for accessory structures.", [
    ("detached_allowed", "prohibited", "2005-04-18", "", PP, "Ch. 420 §420-30B (accessory structures not a dwelling unit) (Ord. 05-13)", "verified", "confirmed by the owner in a browser on ecode360 on 2026-10-24 (the site blocks automated reading); current through Ord. 26-43 (2026-08-24)"),
    ("attached_allowed", "prohibited", "2005-04-18", "", PP, "§420-105 to 420-117 (one principal use/structure; one single-family dwelling)", L, "all residential districts read via rendering"),
], note="Restrictive pilot (owner decision). §420-30B confirmed by the owner from the primary ecode360 page on 2026-10-24.")

MF = "https://library.municode.com/wi/menomonee_falls/codes/code_of_ordinances?nodeId=COOR_CH122ZO_ARTIVUS_DIV5ACUSDEUSSPCO"
muni(["5513351000"], "Menomonee Falls village", PIMP, "coded_source_lead", "2026-03-02",
     "One ADU per single-family parcel, detached and attached, by right in R-1 to R-6/CDD/PRD; at least 600 sq ft; no extra parking; no owner/related rule.", [
    ("detached_allowed", "prohibited", "", "", MF, "§122-400(3), §122-430, Fig. 122-441.1", L, "Municode via search-engine rendering; ZBA staff report 2026-06-04 confirms one home per R-1 lot (URL not recorded)"),
    ("attached_allowed", "prohibited", "", "", MF, "§122-430(a)(1)a.1", L, "Municode via search-engine rendering"),
])

HW = "https://www.zoneomics.com/code/howard-WI"
muni(["5500935950", "5508735950"], "Howard village", PEXP, "coded_source_lead", "2026-07-27",
     "Detached and attached ADUs by right; repeals the §50-868 living-space ban in accessory buildings.", [
    ("detached_allowed", "prohibited", "2011-03-28", "", HW, "Ch. 50 §50-868 (Ord. 2011-7), §50-342", L, "code via mirror; Village Board President report 2026-07-13 (DocumentCenter/View/11523) confirms ADU amendments not completed (verified)"),
    ("attached_allowed", "prohibited", "", "", HW, "§50-342 R-1 permitted uses; R-2 to R-5", L, "guesthouse defined (§50-6) but not listed in any district"),
])

# House size (sq ft) below which a percent-of-house cap stops a 600 sq ft ADU (600 / share), per flagged place.
SIZE_BINDS = {
    "Eau Claire city": "attached: building under 1,500 (600/0.40); detached 20%-of-lot cap binds on lots under 3,000",
    "Oshkosh city": "every ADU: absolute cap of 400 sq ft",
    "Waukesha city": "attached: house under 1,500 (600/0.40); detached: house under 800 (600/0.75)",
    "West Allis city": "detached footprint: principal footprint under 1,200 (600/0.50)",
    "New Berlin city": "principal living area under 1,200 (600/0.50)",
    "Wausau city": "house under 800 (600/0.75)",
    "Oak Creek city": "house under 1,200 (600/0.50)",
    "Mount Pleasant village": "principal GFA under 1,500 (600/0.40)",
    "Mequon city": "house living area under 1,500 (600/0.40)",
    "De Pere city": "secondary suite: principal GFA under 2,000 (600/0.30); cottage 650 footprint is not binding",
    "Fitchburg city": "house floor area under 800 (600/0.75)",
}

# First pass (ordinance_status, AQ-026): does the code have an ADU ordinance at all?
#   mentioned_allowed = a dwelling-unit ADU term (scanner TERMS) appears and the passage allows that use somewhere
#   prohibited        = an ADU term appears only to bar it (or is defined but listed in no district), or, in a
#                       manual reading, the code bars dwellings/living quarters in accessory buildings
#   unmentioned       = no dwelling-unit ADU term found in the text read
# An ADU is a dwelling unit with its own kitchen, sanitation and sleeping facilities for permanent habitation
# (owner decision 2026-10-24). Generic "accessory structure/building/use" wording never counts, and
# second-dwelling words that are not dwelling units (guest house, servants'/domestic-help quarters,
# accessory living quarters, dependency living) are scanner LEAD_TERMS: recorded, not counted.
#   could_not_access  = text not readable (none left after manual reading)
# Automated hits are mapped by the builder: mentions_adu -> mentioned_allowed unless listed in
# FIRST_PASS_HIT_STATUS; no_mention -> unmentioned. Places the scanner could not read (or where it read a
# document that is not the code) take the manual answer below, recorded 2026-10-23 with the original term list.
# The terms added on 2026-10-24 (accessory apartment; lead terms guest house, domestic/servant quarters,
# dependency living, accessory living) were not re-searched in manual places; only hits the readers noted are used.
# name -> (ordinance_status, section of first hit or "", terms, verification, how read)
MANUAL_FIRST_PASS = {
    "Milwaukee city": ("mentioned_allowed", "Table 295-505-2.5", "accessory dwelling;ADU", L, "Ch. 295 subch. 5 PDF read via search-engine rendering (direct fetch 403)"),
    "Madison city": ("mentioned_allowed", "MGO 28.151", "accessory dwelling", V, "adopted ordinance texts via Legistar API (Municode 403)"),
    "Kenosha city": ("unmentioned", "", "", L, "§§3.01-3.32 read via search-engine rendering of Municode; no dwelling-unit term; lead term 'residential quarters for domestic help' (permitted in RS-1, §3.04.A.4) is not counted as an ADU mention (owner definition 2026-10-24)"),
    "Racine city": ("unmentioned", "", "", L, "Ch. 114 district text read via search-engine rendering of Municode; BZA report 1038-24 says code does not allow accessory dwellings"),
    "Appleton city": ("mentioned_allowed", "§23-55", "accessory dwelling;ADU", V, "Ch. 23 Supp. 100 PDF (Feb 2026) read by research agent"),
    "Eau Claire city": ("mentioned_allowed", "17.03.04(B)(2)", "accessory dwelling;ADU", V, "LDO PDF read in a browser (direct fetch 403)"),
    "Janesville city": ("unmentioned", "", "", L, "Ch. 42 read via search extracts only (Municode 403)"),
    "New Berlin city": ("mentioned_allowed", "§275-42 C(3)", "accessory dwelling;family dwelling unit", L, "Zoneomics mirror (Municode 403); bars detached ADUs, allows the attached family dwelling unit"),
    "Wausau city": ("mentioned_allowed", "§23.03.28(6)", "accessory dwelling;in-law", V, "Title 23 read in a browser (Municode 403)"),
    "Beloit city": ("unmentioned", "", "", L, "Ch. 19 via Zoneomics mirror; no dwelling-unit term; lead terms 'private guest houses' and 'employee living quarters' (§6.3.3(a)) are not counted as ADU mentions (owner definition 2026-10-24)"),
    "Greenfield city": ("unmentioned", "", "", L, "Ch. 21 read via search-engine rendering of Municode"),
    "Superior city": ("unmentioned", "", "", V, "Ch. 122 Arts. I, IV, VI searched in a browser (Municode 403)"),
    "Neenah city": ("unmentioned", "", "", L, "Ch. 26 via Zoneomics mirror (Municode 403)"),
    "Muskego city": ("mentioned_allowed", "§400-165", "in-law", L, "ecode360 read via search-engine rendering (403); 'mother-in-law/family unit'"),
    "Mount Pleasant village": ("mentioned_allowed", "§90-110.20(g)", "backyard cottage;secondary dwelling unit", L, "ecode360 read via search-engine rendering (403)"),
    "Mequon city": ("mentioned_allowed", "§58-248", "accessory dwelling;ADU", L, "Ch. 58 read via search-engine rendering of Municode (403)"),
    "Pleasant Prairie village": ("unmentioned", "", "", L, "Ch. 420 incl. Art. XXI definitions read via search-engine rendering of ecode360 (403)"),
    "Menomonee Falls village": ("unmentioned", "", "", L, "Ch. 122 read via search-engine rendering of Municode (403)"),
    "Howard village": ("prohibited", "§50-868", "", L, "Ch. 50 via Zoneomics mirror; §50-868 bars living space in accessory buildings (an accessory-dwelling ban); no dwelling-unit term; lead term 'guesthouse' (§50-6) is defined but listed as a use in no district"),
    "Caledonia village": ("unmentioned", "", "", L, "Title 16 not readable (Municode 403); district text from cached village PDF; the scanned staff report (not code) says the code does not allow ADUs"),
}
# Automated hits whose passage does not allow the use (none so far); name -> (status, reason)
FIRST_PASS_HIT_STATUS = {}
# What the automated scanner actually read, where it was not the current codified chapter.
SCAN_DOC_NOTE = {
    "Green Bay city": "scanned the adopting ordinance G.O. 24-25, not the codified chapter (a hit is guaranteed)",
    "Waukesha city": "scanned adopted Ch. 22.03 text (Ord. 2026-4)",
    "West Allis city": "scanned adopting ordinance O-2022-0024 (a hit is guaranteed)",
    "La Crosse city": "scanned adopting ordinance 5280 (a hit is guaranteed)",
    "Wauwatosa city": "scanned adopting ordinance O-25-25 (a hit is guaranteed)",
    "Sun Prairie city": "scanned adopting ordinance 984 (a hit is guaranteed)",
    "Fitchburg city": "scanned adopting ordinance 2025-O-17 (a hit is guaranteed)",
    "Fond du Lac city": "scanned Zoneomics mirror of Ch. 720 art. IV (ecode360 403)",
    "Oshkosh city": "scanned Wayback copy of city Laserfiche Ch. 30",
    "Sheboygan city": "scanned Ch. 105 as compiled 2023-04-27 (stale; no ADU amendment adopted since, per council minutes); accessory-dwelling ban found at §105-722 ('in no instance shall an accessory use ... be used as a residence'), which the second pass codes prohibited_explicit",
    "West Bend city": "scanned Ch. 17 as codified 2022-02-16 (stale; 2022-2026 amendments not read)",
    "Brookfield city": "no dwelling-unit term; lead terms only (R-1 guest houses incorporated in the house, UC-district servants' quarters), which are not ADU mentions under the owner's definition; second pass: prohibited_implicit",
    "Manitowoc city": "hit is the §15.730 TND definition of secondary dwelling units; second pass: prohibited_implicit for ordinary single-family districts",
}
