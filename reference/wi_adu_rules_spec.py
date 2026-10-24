"""Hand-coded Wisconsin ADU rules (Gate 2). Builder writes reference/wi_adu_rules.csv and wi_rights_exposure.csv."""
R = "2026-10-23"
V, L, U = "verified", "source_lead", "unknown"

# (provision, value, effective_from, effective_to, source_url, source_section, verification, notes)
M = []

def muni(ids, name, cls, basis, as_of, added, rules, note="", default_ok=None):
    M.append(dict(ids=ids, name=name, cls=cls, basis=basis, as_of=as_of, added=added, rules=rules, note=note))

MKE_ORD = "https://milwaukee.legistar1.com/milwaukee/attachments/257d5d3c-c659-463b-8bd3-8d499a6255c2.rtf"
MKE_CPC = "https://milwaukee.legistar1.com/milwaukee/attachments/2caab317-6bf8-4cb3-a0c0-19ed63033977.pdf"
muni(["5507953000", "5513153000", "5513353000"], "Milwaukee city", "restricted", "coded_verified", "2025-08-02",
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
])

MAD = "https://legistar.granicus.com/madison/attachments/3bd8ec23-5475-486c-a0fa-c052e688c5b8.pdf"
muni(["5502548000"], "Madison city", "compliant", "coded_verified", "2025-10-16",
     "None on most single-family parcels; edge cases only (districts where ADUs are not listed, very constrained lots).", [
    ("approval_type", "conditional", "2013-06-04", "2021-12-15", "https://madison.legistar.com/LegislationDetail.aspx?ID=5218928&GUID=692C2A7F-1E48-4779-9367-715C9FD31C50", "MGO 28.151 (2013 code; ORD-13-00098)", V, "every ADU needed conditional use until Dec 2021"),
    ("approval_type", "permitted", "2021-12-16", "", "https://madison.legistar.com/LegislationDetail.aspx?ID=5218928&GUID=692C2A7F-1E48-4779-9367-715C9FD31C50", "ORD-21-00087 (File 68079)", V, "residential, and mixed-use where single-family allowed"),
    ("detached_allowed", "by_right", "2021-12-16", "", MAD, "MGO 28.151", V, ""),
    ("attached_allowed", "by_right", "2021-12-16", "", MAD, "MGO 28.151", V, ""),
    ("owner_occupancy", "ongoing", "2013-06-04", "2024-04-25", "https://webapi.legistar.com/v1/madison/matters/91265/texts/92975", "MGO 28.151 before ORD-24-00022", V, ""),
    ("owner_occupancy", "none", "2024-04-26", "", "https://webapi.legistar.com/v1/madison/matters/91265/texts/92975", "ORD-24-00022 (File 81952)", V, ""),
    ("occupant_restriction", "none", "2021-12-16", "", MAD, "MGO 28.151", V, ""),
    ("max_size_sqft", "1000 (internal; detached building footprint)", "2025-03-08", "", MAD, "ORD-25-00011 (File 86650)", V, "900 sq ft and 2 bedrooms 2021-12-16 to 2025-03-07"),
    ("parking_required", "0", "", "", "https://www.zoneomics.com/code/madison-WI/chapter_10", "Table 28I-3 (snippet)", L, "principal home may still need 1 space outside TOD overlay"),
    ("other", "one attached ADU, or up to two detached ADUs in one structure", "2025-10-16", "", "https://madison.legistar.com/LegislationDetail.aspx?ID=7656026&GUID=F9768184-E06C-4B82-95BE-E43F79D47E7F", "ORD-25-00068 (File 89918)", V, ""),
])

GB24 = "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/15619/1400450/pdf"
GB29 = "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/15619/1400449/pdf"
muni(["5500931000"], "Green Bay city", "restricted", "coded_verified", "2025-12-02",
     "ADUs by right instead of conditional use; removes ongoing owner-occupancy rule; removes 1 required parking space.", [
    ("detached_allowed", "conditional", "", "2025-12-01", GB24, "former carriage-house dwelling rule (struck text in G.O. 24-25)", V, "only above a detached rear garage, R-1/RR, lot +2,500 sq ft, owner-occupied, 1 space"),
    ("detached_allowed", "conditional", "2025-12-02", "", GB29, "G.O. 29-25, Table 44-1 ('C' in R-1, R-2, R-3, RR)", V, "publication date not seen"),
    ("attached_allowed", "conditional", "2025-12-02", "", GB24, "G.O. 24-25, §44-1580(f)", V, ""),
    ("owner_occupancy", "ongoing", "2025-12-02", "", GB24, "§44-1580(f)", V, ""),
    ("occupant_restriction", "none", "2025-12-02", "", GB24, "§44-1580(f)", V, "short-term rental prohibited"),
    ("max_size_sqft", "lesser of 1000 or size of primary building", "2025-12-02", "", GB24, "§44-1580(f)", V, ""),
    ("parking_required", "1", "2025-12-02", "", GB24, "§44-1580(f)", V, ""),
    ("approval_type", "conditional use permit", "2025-12-02", "", GB29, "Table 44-1", V, ""),
])

KEN = "https://library.municode.com/wi/kenosha/codes/zoning_ordinance"
muni(["5505939225"], "Kenosha city", "restricted", "coded_verified", "2026-04-20",
     "Detached and attached ADUs by right in all single-family districts for any occupant; removes domestic-help occupant limit and one-principal-building bar; at least 600 sq ft despite the 840 sq ft / 15% accessory cap; no extra parking.", [
    ("detached_allowed", "by_right", "", "", KEN, "§3.04.A.4 (RS-1 only: residential quarters for domestic help)", V, "borderline: only domestic-help quarters, RS-1 only; prohibited in RR-1-3, RS-2, RS-3, TRD-1; adoption date not found"),
    ("attached_allowed", "prohibited", "", "", KEN, "§3.03.A one principal building per lot", V, "except the RS-1 domestic-help clause"),
    ("occupant_restriction", "related_only", "", "", KEN, "§3.04.A.4", V, "domestic help/employees"),
    ("owner_occupancy", "none", "", "", KEN, "§3.04.A.4", V, "none stated"),
    ("max_size_sqft", "accessory buildings: lesser of 15% of lot or 840, and <= house footprint", "2024-09-16", "", KEN, "§3.03.D.4.d (Ord. 36-24)", V, ""),
    ("parking_required", "unknown", "", "", KEN, "§6.01 not read", U, ""),
], note="Classed restricted because the code names a domestic-help dwelling form; prohibited if such quarters are not counted as an ADU form.")

RAC = "https://library.municode.com/wi/racine/codes/code_of_ordinances?nodeId=PTIIMUCO_CH114ZO_ARTVDIRE_DIV2REDI"
muni(["5510166000"], "Racine city", "prohibited", "coded_verified", "2026-03-03",
     "One detached or attached ADU by right on every R1/R2 single-family lot; at least 600 sq ft; no extra parking; no owner-occupancy or relative rule.", [
    ("detached_allowed", "prohibited", "", "", RAC, "§114-272, §114-292, §114-691 (accessory building may not be used for living)", V, "confirmed by BZA staff report Legistar 1038-24 (2024-11-18)"),
    ("attached_allowed", "prohibited", "", "", RAC, "§114-272, §114-292", V, "pending rewrite ZOrd.0007-26 (introduced 2026-09-11) also has no ADU use"),
])

APP_LEG = "https://cityofappleton.legistar.com/LegislationDetail.aspx?GUID=96A34E37-FF1B-4AE2-B7A9-1E1BF0F8367E&ID=4970068"
muni(["5508702375", "5501502375", "5513902375"], "Appleton city", "compliant", "coded_verified", "2026-02-01",
     "None; already meets the benchmark (ADU plus junior ADU by right, no parking, no owner occupancy).", [
    ("detached_allowed", "prohibited", "", "2021-07-12", APP_LEG, "before Ord. 25-21", L, "pre-2021 text not checked"),
    ("detached_allowed", "by_right", "2021-07-13", "", APP_LEG, "§23-55 (Ord. 25-21); §23-56 JADU (Ord. 26-21)", V, "R-1A, R-1B, R-1C, R-2, R-3"),
    ("attached_allowed", "by_right", "2021-07-13", "", APP_LEG, "§23-55, §23-56", V, ""),
    ("owner_occupancy", "none", "2021-07-13", "", APP_LEG, "§23-55", V, "cannot be sold separately (deed restriction)"),
    ("occupant_restriction", "none", "2021-07-13", "", APP_LEG, "§23-55", V, ""),
    ("max_size_sqft", "ADU+JADU <= principal GFA; JADU <= 500", "2021-07-13", "", APP_LEG, "§23-55, §23-56", V, ""),
    ("parking_required", "0", "2021-07-13", "", APP_LEG, "§23-55", V, ""),
    ("approval_type", "building permit", "2021-07-13", "", APP_LEG, "§23-55", V, ""),
])

WK = "https://legistar2.granicus.com/waukesha/attachments/fb763278-f10c-4d54-91b2-240833e68012.pdf"
WK3 = "https://legistar2.granicus.com/waukesha/attachments/c852c290-1ccf-4801-9967-8d87347537fd.pdf"
WK6 = "https://legistar2.granicus.com/waukesha/attachments/8c8662e7-dfc1-4ece-b405-5a0c1116a477.pdf"
muni(["5513384250"], "Waukesha city", "restricted", "coded_verified", "2026-09-01",
     "Removes 1 required parking space per ADU; guarantees a 600 sq ft detached ADU regardless of house size.", [
    ("detached_allowed", "prohibited", "", "2026-08-31", "https://www.zoneomics.com/code/waukesha-WI", "old Ch. 22, §22.24 RS-1", L, "no ADU or in-law provision in old code (mirror plus March 2026 news)"),
    ("detached_allowed", "by_right", "2026-09-01", "", WK3, "Ch. 22.03(5)(A) use table, RN-1 to RN-4 (Ord. 2026-4, adopted 2026-07-07)", V, ""),
    ("attached_allowed", "by_right", "2026-09-01", "", WK3, "22.03(6)(C)(4)", V, "attached, internal, basement or attic"),
    ("owner_occupancy", "none", "2026-09-01", "", WK3, "22.03(6)(C)(4)", V, "6-month owner rule in May 2025 draft was dropped"),
    ("occupant_restriction", "none", "2026-09-01", "", WK3, "22.03(6)(C)(4)", V, ""),
    ("max_size_sqft", "detached lesser of 1200 or 75% of principal; attached 40% of principal or whole basement/attic", "2026-09-01", "", WK3, "22.03(6)(C)(4)", V, "600 sq ft detached needs house >= 800 sq ft"),
    ("parking_required", "1", "2026-09-01", "", WK6, "Table 22.06(4)(B)(3)", V, ""),
    ("approval_type", "permitted use plus staff site plan and architectural review", "2026-09-01", "", WK, "22.11(4)(B)(2)", V, ""),
])

EC = "https://www.eauclairewi.gov/DocumentCenter/View/1033/Land-Development-Ordinance-PDF"
muni(["5503522300", "5501722300"], "Eau Claire city", "restricted", "coded_verified", "2026-05-04",
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
], note="An August 2026 LDO amendment (DocumentCenter/View/2244) is a scanned PDF and was not read.")

OSH = "https://web.archive.org/web/20251214231347/https://www.oshkoshwi.gov/WebLink/DocView.aspx?id=1183289&dbid=0&repo=Laserfiche"
muni(["5513960500"], "Oshkosh city", "restricted", "coded_verified", "2026-03-31",
     "Raises the 400 sq ft ADU cap so at least 600 sq ft is allowed.", [
    ("detached_allowed", "prohibited", "", "2023-02-27", OSH, "Ch. 30 before 2023 revision", L, "in-family suite inside a house was allowed"),
    ("detached_allowed", "by_right", "2023-02-28", "", OSH, "§30-86(X) [Revised 02.28.23]", V, "'P' in 6 of 20 districts; district mapping source lead"),
    ("attached_allowed", "by_right", "2023-02-28", "", OSH, "§30-22(178), §30-86(X)", V, ""),
    ("owner_occupancy", "none", "2023-02-28", "", OSH, "§30-86(X)", V, "none stated"),
    ("occupant_restriction", "none", "2023-02-28", "", OSH, "§30-86(X)", V, ""),
    ("max_size_sqft", "400", "2023-02-28", "", OSH, "§30-86(X)", V, ""),
    ("parking_required", "0", "2023-02-28", "", OSH, "§30-86(X)", V, "none stated"),
])

JV = "https://library.municode.com/wi/janesville/codes/code_of_ordinances"
muni(["5510537825"], "Janesville city", "prohibited", "coded_verified", "2026-04-27",
     "ADUs by right (detached and attached, at least 600 sq ft, no extra parking, no owner occupancy) in all single-family districts.", [
    ("detached_allowed", "prohibited", "", "", JV, "Ch. 42, §42-353 (one principal building per lot), §42-362, §42-440", V, "text read via search extracts; pending Ch. 46 draft (2026-04-30) would allow ADUs with owner occupancy, not adopted as of 2026-10-23"),
    ("attached_allowed", "prohibited", "", "", JV, "§42-440", V, "two-family by CUP in R1 on lots >= 10,000 sq ft is a duplex path, not an ADU"),
], note="Re-check council action on draft Ch. 46 before freezing at 2026-10-31.")

WA = "https://westalliswi.legistar1.com/westalliswi/attachments/df2ec2d7-5409-4759-a080-5366789281e4.pdf"
muni(["5507985300"], "West Allis city", "restricted", "coded_verified", "2026-02-24",
     "Guarantees a 600 sq ft ADU regardless of house size (removes 50%-of-principal footprint cap); allows attached/internal ADUs by right in RA-1/RA-2.", [
    ("detached_allowed", "prohibited", "", "2022-05-02", WA, "old Ch. 12 (repealed text quoted in O-2022-0024)", V, ""),
    ("detached_allowed", "by_right", "2022-05-03", "", WA, "Ch. 19 §19.36(1) (O-2022-0024)", V, "limited use, 1 per lot, all residential districts"),
    ("attached_allowed", "conditional", "2022-05-03", "", WA, "§19.16, §19.33", V, "internal/attached second unit = 2-unit dwelling; limited in RA-1/RA-2 to lots by commercial districts (interpretation)"),
    ("owner_occupancy", "none", "2022-05-03", "", WA, "Ch. 19", V, ""),
    ("occupant_restriction", "none", "2022-05-03", "", WA, "Ch. 19", V, ""),
    ("max_size_sqft", "footprint <= 50% of principal, max 800", "2023-06-06", "", "https://westalliswi.legistar1.com/westalliswi/attachments/c1e7f426-a56f-412e-bac2-b38e83565261.pdf", "O-2023-0031", V, "700 sq ft cap 2022-05-03 to 2023-06-05"),
    ("parking_required", "0", "2023-06-06", "", "https://westalliswi.legistar1.com/westalliswi/attachments/c1e7f426-a56f-412e-bac2-b38e83565261.pdf", "§19.44 (maximums only)", V, ""),
    ("approval_type", "design review permit plus building permit", "2022-05-03", "", WA, "§19.36", V, ""),
])

LAX = "https://legistar.granicus.com/CityofLaCrosse/attachments/239dbc28-943b-4645-9f22-e87475d777da.docx"
muni(["5506340775"], "La Crosse city", "restricted", "coded_verified", "2024-02-17",
     "Attached/internal ADUs by right; removes ongoing owner-occupancy rule and deed restriction.", [
    ("detached_allowed", "prohibited", "", "2024-02-16", LAX, "§115-390(1)(d)(3) plumbing ban in accessory structures (amended by Ord. 5280)", V, ""),
    ("detached_allowed", "by_right", "2024-02-17", "", LAX, "§115-405 (Ord. 5280, Legistar 23-1243, published 2024-02-17)", V, "R-1 to R-4, Washburn Residential"),
    ("attached_allowed", "prohibited", "2024-02-17", "", LAX, "§115-405", V, "freestanding, converted garage or garage addition only"),
    ("owner_occupancy", "ongoing", "2024-02-17", "", LAX, "§115-405", V, "deed restriction before permit"),
    ("occupant_restriction", "none", "2024-02-17", "", LAX, "§115-405", V, ""),
    ("max_size_sqft", "lesser of 900 or house floor area", "2024-02-17", "", LAX, "§115-405", V, ""),
    ("parking_required", "0", "2024-02-17", "", LAX, "§115-405", V, ""),
    ("approval_type", "building permit (permitted accessory use)", "2024-02-17", "", LAX, "§115-405", V, ""),
])

SHEB = "https://mccmeetingspublic.blob.core.usgovcloudapi.net/sheboygnwi-meet-1ab88e5a89ad4af6836be2c56109cdb0/ITEM-Attachment-001-015d62d52b424fc985217ee1b0ae1f13.pdf"
muni(["5511772975"], "Sheboygan city", "prohibited", "coded_verified", "2026-04-08",
     "Detached and attached ADUs by right where none are allowed.", [
    ("detached_allowed", "prohibited", "2020-02-07", "", SHEB, "Ch. 105, §105-722 (accessory use never a residence), §105-202", V, "Gen. Ord. 37-25-26 (Dec 2025) and 39-25-26 (Mar 2026) not adopted; referred 2026-04-08"),
    ("attached_allowed", "prohibited", "2020-02-07", "", SHEB, "§105-7 (no split except two-flat)", V, ""),
], note="Gate 1 listed Sheboygan as a December 2025 liberalizer; the ordinance was laid over and referred, never adopted (source lead after April 2026).")

TOSA = "https://wauwatosacitywi.legistar1.com/wauwatosacitywi/attachments/f54c270b-576f-4e05-a954-36755d2e4f9c.pdf"
muni(["5507984675"], "Wauwatosa city", "compliant", "coded_verified", "2025-11-18",
     "None beyond current code (edge case: houses under 600 sq ft).", [
    ("detached_allowed", "by_right", "2019-06-18", "", "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/16684/962746/pdf?forceDownload=true", "§24.10.075 (O-19-11)", V, ""),
    ("attached_allowed", "by_right", "2019-06-18", "", "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/16684/962746/pdf?forceDownload=true", "§24.10.075 (O-19-11)", V, ""),
    ("max_size_sqft", "lesser of 650 or 49% of house", "2019-06-18", "2022-09-19", "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/16684/962746/pdf?forceDownload=true", "O-19-11", V, ""),
    ("max_size_sqft", "lesser of 900 or house GFA", "2022-09-20", "2025-11-17", "https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/wauwatosa/ordinances/documents/1714691803_O-22-24.pdf", "O-22-24", V, ""),
    ("max_size_sqft", "lesser of 1000 or house GFA", "2025-11-18", "", TOSA, "§24.10.075 recreated by O-25-25", V, "effective on publication; publication date not found"),
    ("owner_occupancy", "none", "2019-06-18", "", TOSA, "§24.10.075", V, ""),
    ("occupant_restriction", "none", "2019-06-18", "", TOSA, "§24.10.075", V, ""),
    ("parking_required", "0", "2019-06-18", "", TOSA, "§24.10.075", V, ""),
    ("approval_type", "building permit", "2019-06-18", "", TOSA, "§24.10.075", V, ""),
])

FDL = "https://www.fdl.wi.gov/"
muni(["5503926275"], "Fond du Lac city", "restricted", "coded_verified", "2026-03-25",
     "Removes ongoing owner-occupancy rule; removes 1 extra parking space; lifts footprint cap for small houses.", [
    ("detached_allowed", "prohibited", "", "2025-02-25", FDL, "Ch. 720 Schedule II before Ord. 3809 (no ADU row); City Council minutes 2025-02-26", V, ""),
    ("detached_allowed", "by_right", "2025-02-26", "", FDL, "§720-11C(29), Schedule II ('SC' in R-1 to R-4) (Ord. 3809)", V, "permitted with special conditions"),
    ("attached_allowed", "by_right", "2025-02-26", "", FDL, "§720-11C(29)", V, ""),
    ("owner_occupancy", "ongoing", "2025-02-26", "", FDL, "§720-11C(29)", V, ""),
    ("occupant_restriction", "none", "2025-02-26", "", FDL, "§720-11C(29)", V, "rentals >= 30 days"),
    ("max_size_sqft", "detached lesser of 800 or house footprint; attached greater of 800 or 50% of footprint; <= 2 bedrooms", "2025-02-26", "", FDL, "§720-11C(29)", V, ""),
    ("parking_required", "1", "2025-02-26", "", FDL, "§720-11C(29)", V, ""),
    ("approval_type", "administrative (special conditions)", "2025-02-26", "", FDL, "Art. VI not read", L, ""),
])

NB = "https://www.zoneomics.com/code/new-berlin-WI/chapter_5"
muni(["5513356375"], "New Berlin city", "restricted", "coded_source_lead", "2026-01-27",
     "Detached and semi-detached ADUs; at least 600 sq ft (50%-of-house cap); ADUs outside agricultural/single-family districts; removes owner-occupancy, related-occupant and 2-occupant rules; no extra parking.", [
    ("detached_allowed", "prohibited", "2013-06-17", "", NB, "§275-42 C(3); §275-42 B(1)(a)[2][b][iii]", L, "confirmed by City Sheds guidance PDF (verified)"),
    ("attached_allowed", "by_right", "2013-06-17", "", NB, "§275-42 C(3) family dwelling unit, zoning permit §275-24", L, "agricultural and single-family districts only"),
    ("owner_occupancy", "ongoing", "2013-06-17", "", NB, "§275-42 C(3)", L, ""),
    ("occupant_restriction", "related_only", "2013-06-17", "", NB, "§275-42 C(3)", L, "max 2 occupants; deed restriction"),
    ("max_size_sqft", "50% of principal living area", "2013-06-17", "", NB, "§275-42 C(3)", L, ""),
    ("parking_required", "unknown", "", "", NB, "Table 275-57-1", U, ""),
    ("approval_type", "administrative zoning permit", "2013-06-17", "", NB, "§275-24", L, ""),
], note="Coded at Gate 1 (POLICY_EVIDENCE_MAP section 3); Municode blocked; code version through Ord. 2717 (2026-01-27).")

WAU = "https://library.municode.com/wi/wausau/codes/code_of_ordinances?nodeId=TIT23ZO_ARTIIILAUSRE"
muni(["5507384475"], "Wausau city", "restricted", "coded_verified", "2026-07-14",
     "Detached and attached ADUs by right (not conditional use) in all single-family districts incl. DR-6; removes owner-occupancy; at least 600 sq ft always allowed (800 sq ft / 75% cap).", [
    ("detached_allowed", "conditional", "2020-01-01", "", WAU, "§23.03.05 use table; §23.03.28(6)", V, "RH-35, SR-2, SR-3, SR-5, SR-7, TF-10, TRD-12; Title 23 adopted 2020 (date approximate, source lead)"),
    ("attached_allowed", "conditional", "2020-01-01", "", WAU, "§23.03.28(6)", V, "in-family suite §23.03.28(7) by right but family only, internal connection"),
    ("owner_occupancy", "ongoing", "2020-01-01", "", WAU, "§23.03.28(6)(e)1", V, ""),
    ("occupant_restriction", "none", "2020-01-01", "", WAU, "§23.03.28(6)", V, ""),
    ("max_size_sqft", "lesser of 800 or 75% of house", "2020-01-01", "", WAU, "§23.03.28(6)", V, ""),
    ("parking_required", "unknown", "", "", WAU, "§23.03.28(6) silent; house needs 2", U, ""),
    ("approval_type", "conditional use permit", "2020-01-01", "", WAU, "§23.03.05", V, ""),
], note="Pre-2020 rules not found.")

BF = "https://www.codepublishing.com/WI/Brookfield/html/Brookfield17/Brookfield1728.html"
muni(["5513310025"], "Brookfield city", "prohibited", "coded_verified", "2026-02-17",
     "One ADU (separate dwelling with kitchen) per single-family parcel, detached and attached, by right in R-1 to R-3; at least 600 sq ft; no extra parking; no owner-occupancy or related-occupant rule.", [
    ("detached_allowed", "prohibited", "", "", BF, "§17.04.020 (one-family dwelling), §17.28.010(F)(6)", V, "separate guest houses only on lots > 3 acres with Plan Commission review; 'guest house' undefined"),
    ("attached_allowed", "prohibited", "", "", BF, "§17.28.010(F)(6)", V, "guest houses physically incorporated into the house are allowed but are guest space, not a second unit"),
], note="Borderline: restricted if undefined guest houses are counted as an ADU form. Mayor re-elected 2026-04-07 opposing ADUs (source lead).")

BEL = "https://www.zoneomics.com/code/beloit-WI"
muni(["5510506500"], "Beloit city", "restricted", "coded_source_lead", "2026-06-01",
     "Rentable ADUs by right on every single-family parcel, detached and attached; removes guest/employee no-rent limit and 12,000 sq ft lot minimum; exempts ADUs from the 1,000 sq ft minimum dwelling size and the single-to-multi conversion ban.", [
    ("detached_allowed", "by_right", "2001-01-01", "", BEL, "Ch. 19 §6.3.3(a) private guest houses / detached employee quarters", L, "lots >= 12,000 sq ft and 85 ft wide; Ord. 2946 (2001), date approximate"),
    ("attached_allowed", "prohibited", "2025-06-02", "", BEL, "§6.2.11(b)(8) (Ord. 3868) conversion ban except PUD", L, ""),
    ("occupant_restriction", "related_only", "2001-01-01", "", BEL, "§11.3.101 guest house not rented", L, "guests or employees"),
    ("min_lot_size", "12000", "2001-01-01", "", BEL, "§6.3.3(a)", L, ""),
    ("max_size_sqft", "accessory buildings greater of 720 or 10% of lot, <= 1200 each", "2016-04-27", "", BEL, "§6.3.4(d) (Ord. 3574)", L, ""),
], note="Borderline: prohibited if non-rented guest houses and employee quarters are not counted as an ADU form.")

GF = "https://library.municode.com/wi/greenfield/codes/code_of_ordinances?nodeId=CH21ZOCO_PT4ZODIDIESDIUSRE_DIV21.04.0800ACTEUSSTRE_21.04.0802DESTACUSREDI"
muni(["5507931175"], "Greenfield city", "prohibited", "coded_verified", "2026-10-23",
     "One ADU per single-family parcel, detached and attached, by right in R-1 to R-4B; at least 600 sq ft; no extra parking; no owner-occupancy or related-occupant rule.", [
    ("detached_allowed", "prohibited", "", "", GF, "§21.03.0206 one principal building; Table 21.04.0602; §21.03.0210", V, "§§21.03.0206/0210 via mirror"),
    ("attached_allowed", "prohibited", "", "", GF, "Table 21.04.0602 (two-family only in R-4, R-4A, R-4B, MFR, PUD)", V, ""),
], note="Municode currency date not shown; rules_as_of is the access date.")

FR = "https://www.franklinwi.gov/Files/Planning/UDO-Rewrite-2025/2025-UDO-Rewrite-Text.pdf"
muni(["5507927300"], "Franklin city", "restricted", "coded_verified", "2025-06-09",
     "Detached and attached ADUs by right in all residential districts (currently conditional use); removes owner primary-residence requirement.", [
    ("detached_allowed", "prohibited", "1998-01-01", "2025-06-08", "https://franklinwi.gov/Files/Planning/UDOTextAmendmentOrd/UDO_UpdatedVersion_Dec192014.pdf", "Ord. 98-1493 UDO (one principal building except R-1E)", V, "R-1E allowed guest/servant/caretaker quarters; effective_from approximate"),
    ("detached_allowed", "conditional", "2025-06-09", "", FR, "Table 15-3-04(B) (Ord. 2025-2675)", V, "all five residential districts"),
    ("attached_allowed", "conditional", "2025-06-09", "", FR, "Table 15-3-04(B); internal ADU 'P' by right", V, ""),
    ("owner_occupancy", "ongoing", "2025-06-09", "", FR, "§15-4-13(A)(12), (B)(4)", V, ""),
    ("occupant_restriction", "none", "2025-06-09", "", FR, "§15-4-13", V, ""),
    ("max_size_sqft", "greater of 25% of house or 1200", "2025-06-09", "", FR, "§15-4-13(A)(5), (B)(2)", V, ""),
    ("parking_required", "0", "2025-06-09", "", FR, "§15-5-01(A)(1) maximums only", V, ""),
    ("approval_type", "conditional use permit (internal: permit)", "2025-06-09", "", FR, "Table 15-3-04(B)", V, ""),
])

OC = "https://assets.parkingreform.org/assets/7d1088f1-4f0b-4f6a-a368-d7a3b6c4d398/oak-creek-wisconsin-united-states-attachment.pdf"
muni(["5507958800"], "Oak Creek city", "restricted", "coded_verified", "2026-04-06",
     "ADUs by right (currently conditional use) in all single-family districts incl. ER/Rs-5/Rd-1; standalone detached ADUs (currently only above/within an existing garage); removes owner-occupancy; at least 600 sq ft always allowed; removes extra ADU parking.", [
    ("detached_allowed", "conditional", "2022-03-15", "", OC, "§17.0414(b)(4) (only above or within an existing detached garage)", V, "Rs-1 to Rs-4 only (Table 17.0304(b))"),
    ("attached_allowed", "conditional", "2022-03-15", "", OC, "§17.0414", V, ""),
    ("owner_occupancy", "ongoing", "2022-03-15", "", OC, "§17.0414(b)(1)", V, ""),
    ("occupant_restriction", "none", "2022-03-15", "", OC, "§17.0414", V, ""),
    ("max_size_sqft", "lesser of 800 or 50% of house", "2022-03-15", "", OC, "§17.0414(b)(2)", V, ""),
    ("parking_required", "1", "2022-03-15", "", OC, "§17.0414(b)(7) (in addition to principal; at least 1)", V, ""),
    ("approval_type", "conditional use permit", "2022-03-15", "", OC, "§17.0804(e)", V, ""),
], note="Pre-2022 rules not found; ordinance number of the 2022 rewrite not found.")

MAN = "https://www.codepublishing.com/WI/Manitowoc/html/Manitowoc15/Manitowoc15110.html"
muni(["5507148500"], "Manitowoc city", "prohibited", "coded_verified", "2026-09-30",
     "Detached and attached ADUs by right where none are allowed.", [
    ("detached_allowed", "prohibited", "", "", MAN, "Ch. 15 (no ADU text; R-2/R-3 single-family)", V, "2023 ADU draft PC 19-2023: no action; Ch. 35 discussion draft (2026-08-14) not adopted"),
    ("attached_allowed", "prohibited", "", "", MAN, "Ch. 15", V, ""),
])

WB = "https://cms9files.revize.com/westbend/17%20Chapter%20Municipal%20Code-%201.pdf"
muni(["5513185350"], "West Bend city", "prohibited", "coded_source_lead", "2022-02-16",
     "One ADU per single-family parcel, detached and attached, by right, at least 600 sq ft, no extra parking, no owner/related rule (overrides one-principal-structure rule and 720 sq ft accessory cap).", [
    ("detached_allowed", "prohibited", "", "", WB, "Ch. 17 §17.09(6)(b), §17.15(1), §17.44(57)", V, "codified text dated 2022-02-16; 2022-2026 amendments not read (site 403)"),
    ("attached_allowed", "prohibited", "", "", WB, "§17.44(57) one family", V, ""),
])

SP = "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/13968/1423544/pdf"
muni(["5502578600"], "Sun Prairie city", "restricted", "coded_verified", "2026-05-08",
     "Extends ADUs to ER-1 and RH-35 single-family parcels; makes the special-use step a plain permit.", [
    ("detached_allowed", "prohibited", "", "2026-05-07", SP, "§17.16.140 before Ord. 984 (accessory buildings never a residence)", V, "whether ADUs were allowed before an earlier code is not verified"),
    ("attached_allowed", "prohibited", "", "2026-05-07", SP, "§17.16.140 before Ord. 984", V, ""),
    ("detached_allowed", "conditional", "2026-05-08", "", SP, "§17.16.140(33) special use (Ord. 984, adopted 2026-05-05, published 2026-05-08)", V, "special use: staff review, no hearing; SR-4, MR-8, UR-12, NC, UC, CC, PD; not ER-1, RH-35"),
    ("attached_allowed", "conditional", "2026-05-08", "", SP, "§17.16.140(33)", V, ""),
    ("owner_occupancy", "none", "2026-05-08", "", SP, "§17.16.140(33)", V, ""),
    ("occupant_restriction", "none", "2026-05-08", "", SP, "§17.16.140(33)", V, ""),
    ("max_size_sqft", "1000 (attached; detached footprint)", "2026-05-08", "", SP, "§17.16.140(33)", V, "one attached or two detached"),
    ("parking_required", "0", "2026-05-08", "", SP, "§17.16.140(33)", V, ""),
    ("approval_type", "special use (§17.16.020(C))", "2026-05-08", "", SP, "§17.16.020(C)", V, ""),
])

SUP = "https://library.municode.com/wi/superior/codes/code_of_ordinances?nodeId=PTIICOOR_CH122ZO"
muni(["5503178650"], "Superior city", "prohibited", "coded_verified", "2025-12-02",
     "Detached and attached ADUs by right on single-family parcels where none are allowed.", [
    ("detached_allowed", "prohibited", "", "", SUP, "Ch. 122 Arts. I, IV, VI (no ADU provision)", V, "pending SRF zoning rewrite draft (Dec 2025) adds accessory dwellings; not adopted"),
    ("attached_allowed", "prohibited", "", "", SUP, "Ch. 122", V, ""),
])

STP = "https://www.stevenspoint.com/DocumentCenter/View/769/Chapter-23---Zoning--Floodplain"
muni(["5509777200"], "Stevens Point city", "restricted", "coded_verified", "2026-05-05",
     "ADUs by right (not conditional use); allows attached/internal ADUs; removes owner-occupancy; removes 1 parking space; removes the single-family-minimum / 10,000 sq ft R-3 lot requirement.", [
    ("detached_allowed", "conditional", "", "", STP, "§23.01(15)(b)", V, "R-LD, R-1 to R-5; adoption ~2022 (source lead), ordinance number not found"),
    ("attached_allowed", "prohibited", "", "", STP, "§23.01(15) (ADU defined as detached)", V, ""),
    ("owner_occupancy", "ongoing", "", "", STP, "§23.01(15)(g)", V, ">= 10 months/yr, recorded agreement"),
    ("occupant_restriction", "none", "", "", STP, "§23.01(15)", V, ""),
    ("min_lot_size", "district single-family minimum; 10000 in R-3", "", "", STP, "§23.01(15)", V, ""),
    ("max_size_sqft", "unknown (Ch. 30 detached accessory limit)", "", "", STP, "§23.01(15)", U, ""),
    ("parking_required", "1", "", "", STP, "§23.01(17)(c)(3)", V, ""),
    ("approval_type", "conditional use permit", "", "", STP, "§23.01(15)(b)", V, ""),
])

NEE = "https://www2.ci.neenah.wi.us/committees.nsf/0/740d7c8b6bbec18886258c6f005576e1/$FILE/A%2020250429PC.pdf"
muni(["5513955750"], "Neenah city", "prohibited", "coded_source_lead", "2025-09-03",
     "Detached and attached ADUs by right where none are allowed.", [
    ("detached_allowed", "prohibited", "2014-08-06", "", NEE, "Ch. 26 §26-148 R-1 one single-family dwelling (Ord. 2014-14); §21-19 accessory building not a dwelling (Ord. 2023-07)", V, "PC minutes 2025: ADUs 'currently prohibited'; current text via mirror; no adoption found in 2026 PC/CC packets"),
    ("attached_allowed", "prohibited", "2014-08-06", "", NEE, "§26-148", V, ""),
], note="'Never adopted through Oct 2026' rests on absence in packets read; minutes search requires login.")

FIT = "https://fitchburgwi.gov/DocumentCenter/View/29094/2025-O-17"
muni(["5502525950"], "Fitchburg city", "compliant", "coded_verified", "2025-09-10",
     "Little or none; at most guarantees 600 sq ft where the 75%-of-house cap binds (houses under 800 sq ft) and confirms no parking minimum.", [
    ("attached_allowed", "conditional", "", "2025-09-09", "https://library.municode.com/wi/fitchburg/codes/code_of_ordinances?nodeId=TIIILAUSDE_CH22ZO_ARTIIREDI", "R-L, R-LM dependency living arrangements", V, "<= 750 sq ft, owner-occupied, caregiver/dependent occupant, interior door"),
    ("owner_occupancy", "ongoing", "", "2025-09-09", "https://library.municode.com/wi/fitchburg/codes/code_of_ordinances?nodeId=TIIILAUSDE_CH22ZO_ARTIIREDI", "dependency living arrangements", V, ""),
    ("detached_allowed", "by_right", "2025-09-10", "", FIT, "Sec. 22-230 (Ord. 2025-O-17, adopted 2025-09-09)", V, "effective day after publication (date approximate)"),
    ("attached_allowed", "by_right", "2025-09-10", "", FIT, "Sec. 22-230", V, ""),
    ("owner_occupancy", "none", "2025-09-10", "", FIT, "Sec. 22-230", V, "cannot be sold separately"),
    ("occupant_restriction", "none", "2025-09-10", "", FIT, "Sec. 22-230", V, ""),
    ("max_size_sqft", "75% of house floor area", "2025-09-10", "", FIT, "Sec. 22-230", V, ""),
    ("parking_required", "unknown", "", "", FIT, "Sec. 22-230 silent; Sec. 22-609", U, "leaning none"),
], note="Compliant with caveats: parking unknown; 75% cap binds on houses under 800 sq ft.")

MUS = "https://ecode360.com/29722805"
muni(["5513355275"], "Muskego city", "restricted", "coded_verified", "2026-03-24",
     "Detached ADUs by right (currently conditional, employee/relative only, no rental, 1,200 sq ft minimum); attached/internal ADUs by right without Plan Commission review; removes related-occupant and no-rental restrictions.", [
    ("attached_allowed", "conditional", "2009-05-12", "", MUS, "§400-165 mother-in-law/family unit (Plan Commission plan review)", V, "read via search rendering of ecode360"),
    ("detached_allowed", "conditional", "2009-05-12", "", MUS, "§400-172(A),(B)", V, "employee/relative quarters or guesthouse, >= 1,200 sq ft, no rental"),
    ("occupant_restriction", "related_only", "2009-05-12", "", MUS, "§400-165(C)", V, ""),
    ("owner_occupancy", "unknown", "", "", MUS, "§400-165", U, "no explicit rule"),
    ("max_size_sqft", "800 (internal unit)", "2009-05-12", "", MUS, "§400-165", V, ""),
    ("approval_type", "Plan Commission plan review / conditional use", "2009-05-12", "", MUS, "§400-165, §400-172", V, ""),
])

MEQ = "https://library.municode.com/wi/mequon/codes/code_of_ordinances?nodeId=PTIICOOR_CH58PLDERE_ARTIVZO_DIV3REDI_SDIIUSRE"
muni(["5508951150"], "Mequon city", "restricted", "coded_verified", "2025-12-09",
     "Detached ADUs; attached ADUs by right instead of conditional use in all single-family districts incl. R-5; removes ongoing owner-occupancy and family/caretaker-only occupancy; at least 600 sq ft (40% cap); confirms no extra parking.", [
    ("detached_allowed", "prohibited", "2021-06-08", "", MEQ, "§58-248(e)(1), §58-415", V, "guesthouse CUP (no kitchen, no rental) is not an ADU"),
    ("attached_allowed", "conditional", "2021-06-08", "", MEQ, "§58-248 (Ord. 2021-1591)", V, "R-1 to R-4 only"),
    ("owner_occupancy", "ongoing", "2021-06-08", "", MEQ, "§58-248(e)(2)", V, ""),
    ("occupant_restriction", "related_only", "2021-06-08", "", MEQ, "§58-248(e)(3)", V, "family, dependent, caretaker"),
    ("max_size_sqft", "40% of house living area", "2021-06-08", "", MEQ, "§58-248(e)(5)", V, ""),
    ("parking_required", "unknown", "", "", MEQ, "§58-441", U, ""),
    ("approval_type", "conditional use (basement units administrative with covenant)", "2021-06-08", "", MEQ, "§58-248(e)(9)", V, ""),
])

DP = "https://www.deperewi.gov/egov/documents/1703171468_81245.pdf"
muni(["5500919775"], "De Pere city", "restricted", "coded_verified", "2026-07-21",
     "Removes ongoing owner-occupancy/deed-restriction rule; lifts the 30%-of-house cap on internal suites.", [
    ("detached_allowed", "by_right", "2023-01-01", "", DP, "Ch. 14 §14-27 backyard cottage", V, "R1, R2, RM-1, RM-2; pre-2023 status not determined"),
    ("attached_allowed", "by_right", "2023-01-01", "", DP, "§14-78(13) secondary suite", V, "cottage or suite, not both"),
    ("owner_occupancy", "ongoing", "2023-01-01", "", DP, "§14-27, §14-78(13)", V, "deed restriction"),
    ("occupant_restriction", "none", "2023-01-01", "", DP, "§14-27", V, ""),
    ("max_size_sqft", "cottage 650 footprint; suite 30% of principal GFA", "2023-01-01", "", DP, "§14-27, §14-78(13)", V, ""),
    ("parking_required", "0", "2023-01-01", "", DP, "§14-27", V, ""),
    ("approval_type", "permit", "2023-01-01", "", DP, "§14-27", V, ""),
])

MTP = "https://ecode360.com/36325067"
muni(["5510154875"], "Mount Pleasant village", "restricted", "coded_verified", "2026-10-23",
     "Guarantees at least 600 sq ft regardless of house size (replaces 40% cap); removes the suite one-rental-unit rule; confirms no extra parking for cottages.", [
    ("detached_allowed", "by_right", "2020-06-08", "", MTP, "§90-110.20(g) backyard cottage; Table 90-310-1", V, "Ord. 19-2020 code rewrite; ADU origin date source lead; restated Ord. 09-2025"),
    ("attached_allowed", "by_right", "2020-06-08", "", "https://ecode360.com/36325586", "§90-330.110 secondary suite", V, ""),
    ("owner_occupancy", "ongoing", "2020-06-08", "", "https://ecode360.com/36325586", "§90-330.110(l) only one unit may be rented", V, "de facto; cottages need deed restriction"),
    ("occupant_restriction", "none", "2020-06-08", "", MTP, "§90-110.20(g)", V, "combined one-household cap"),
    ("max_size_sqft", "40% of principal GFA", "2020-06-08", "", MTP, "§90-110.20(g), §90-330.110", V, ""),
    ("parking_required", "0 (suite); unknown (cottage)", "2020-06-08", "", "https://ecode360.com/36325586", "§90-330.110", V, ""),
    ("approval_type", "zoning/building permit", "2020-06-08", "", MTP, "§90-110.20(g)", V, ""),
])

CAL = "https://data.zoninghub.com/viewfile.aspx?fileid=110664"
muni(["5510111950"], "Caledonia village", "prohibited", "coded_verified", "2026-09-28",
     "Detached and attached ADUs by right on single-family lots (none now; a pending draft would be conditional use only).", [
    ("detached_allowed", "prohibited", "", "", CAL, "Plan Commission staff report 2026-09-28 (application 041-2026); Title 16 §16-6-3 to 16-6-7", V, "district text source lead (cached PDF)"),
    ("attached_allowed", "prohibited", "", "", CAL, "staff report 2026-09-28", V, "staff directed to draft conditional-use ADUs"),
])

PP = "https://ecode360.com/36640696"
muni(["5505963300"], "Pleasant Prairie village", "prohibited", "coded_verified", "2026-08-24",
     "Detached and attached ADUs by right in all single-family districts (R-1 to R-6, R-4.5, A-2); repeals the §420-30B dwelling ban for accessory structures.", [
    ("detached_allowed", "prohibited", "2005-04-18", "", PP, "Ch. 420 §420-30B (accessory structures not a dwelling unit) (Ord. 05-13)", V, "read via search rendering and mirror; current through Ord. 26-43"),
    ("attached_allowed", "prohibited", "2005-04-18", "", PP, "§420-105 to 420-117 (one principal use/structure; one single-family dwelling)", V, "all residential districts read"),
])

MF = "https://library.municode.com/wi/menomonee_falls/codes/code_of_ordinances?nodeId=COOR_CH122ZO_ARTIVUS_DIV5ACUSDEUSSPCO"
muni(["5513351000"], "Menomonee Falls village", "prohibited", "coded_verified", "2026-03-02",
     "One ADU per single-family parcel, detached and attached, by right in R-1 to R-6/CDD/PRD; at least 600 sq ft; no extra parking; no owner/related rule.", [
    ("detached_allowed", "prohibited", "", "", MF, "§122-400(3), §122-430, Fig. 122-441.1", V, "ZBA staff report 2026-06-04 confirms one home per R-1 lot"),
    ("attached_allowed", "prohibited", "", "", MF, "§122-430(a)(1)a.1", V, ""),
])

HW = "https://www.zoneomics.com/code/howard-WI"
muni(["5500935950", "5508735950"], "Howard village", "prohibited", "coded_source_lead", "2026-07-27",
     "Detached and attached ADUs by right; repeals the §50-868 living-space ban in accessory buildings.", [
    ("detached_allowed", "prohibited", "2011-03-28", "", HW, "Ch. 50 §50-868 (Ord. 2011-7), §50-342", L, "code via mirror; Village Board President report 2026-07-13 (DocumentCenter/View/11523) confirms ADU amendments not completed (verified)"),
    ("attached_allowed", "prohibited", "", "", HW, "§50-342 R-1 permitted uses; R-2 to R-5", L, "guesthouse defined (§50-6) but not listed in any district"),
])

# Manual first-pass results where the automated GET could not read code text.
# name -> (result yes/no, section of first hit or "", terms, verification, how read)
MANUAL_MENTIONS = {
    "Milwaukee city": ("yes", "Table 295-505-2.5", "accessory dwelling;ADU", V, "Ch. 295 subch. 5 PDF read via search-engine rendering (direct fetch 403)"),
    "Madison city": ("yes", "MGO 28.151", "accessory dwelling", V, "adopted ordinance texts via Legistar API (Municode 403)"),
    "Kenosha city": ("no", "", "", V, "§§3.01-3.32 read via search-engine rendering of Municode; only 'residential quarters for domestic help'"),
    "Racine city": ("no", "", "", V, "Ch. 114 district text read via rendering of Municode; BZA report 1038-24 says code does not allow accessory dwellings"),
    "Appleton city": ("yes", "§23-55", "accessory dwelling;ADU", V, "Ch. 23 Supp. 100 PDF (Feb 2026) read by research agent"),
    "Eau Claire city": ("yes", "17.03.04(B)(2)", "accessory dwelling;ADU", V, "LDO PDF read in a browser (direct fetch 403)"),
    "Janesville city": ("no", "", "", L, "Ch. 42 read via search extracts only (Municode 403)"),
    "New Berlin city": ("yes", "§275-42 C(3)", "accessory dwelling;family dwelling unit", L, "Zoneomics mirror (Municode 403); mentions and prohibits detached ADUs"),
    "Wausau city": ("yes", "§23.03.28(6)", "accessory dwelling;in-law", V, "Title 23 read in a browser (Municode 403)"),
    "Brookfield city": ("no", "", "", V, "Title 17 read by research agent on codepublishing (403 from scanner); only 'guest houses'"),
    "Beloit city": ("no", "", "", L, "Ch. 19 via Zoneomics mirror; only private guest houses and employee living quarters"),
    "Greenfield city": ("no", "", "", V, "Ch. 21 read via rendering of Municode"),
    "Manitowoc city": ("no", "", "", V, "Ch. 15 read by research agent on codepublishing (403 from scanner)"),
    "Superior city": ("no", "", "", V, "Ch. 122 Arts. I, IV, VI searched in a browser (Municode 403)"),
    "Neenah city": ("no", "", "", L, "Ch. 26 via Zoneomics mirror (Municode 403)"),
    "Muskego city": ("yes", "§400-165", "in-law", V, "ecode360 read via search-engine rendering (403); 'mother-in-law/family unit'"),
    "Mount Pleasant village": ("yes", "§90-110.20(g)", "backyard cottage;secondary dwelling unit", V, "ecode360 read via search-engine rendering (403)"),
    "Mequon city": ("yes", "§58-248", "accessory dwelling;ADU", V, "Ch. 58 read via rendering of Municode (403)"),
    "Pleasant Prairie village": ("no", "", "", V, "Ch. 420 incl. Art. XXI definitions read via rendering of ecode360 (403)"),
    "Menomonee Falls village": ("no", "", "", V, "Ch. 122 read via rendering of Municode (403)"),
    "Howard village": ("no", "", "", L, "Ch. 50 via Zoneomics mirror; only 'guesthouse' (defined, not a listed use)"),
    "Caledonia village": ("no", "", "", L, "Title 16 not readable (Municode 403); district text from cached village PDF; staff report 2026-09-28 says code does not allow ADUs"),
}
# Automated hits that came from an amending ordinance or staff report rather than the codified chapter.
SCAN_DOC_NOTE = {
    "Green Bay city": "scanned the adopting ordinance G.O. 24-25, not the codified chapter",
    "Waukesha city": "scanned adopted Ch. 22.03 (Ord. 2026-4)",
    "West Allis city": "scanned adopting ordinance O-2022-0024",
    "La Crosse city": "scanned adopting ordinance 5280",
    "Wauwatosa city": "scanned adopting ordinance O-25-25",
    "Sun Prairie city": "scanned adopting ordinance 984",
    "Fitchburg city": "scanned adopting ordinance 2025-O-17",
    "Fond du Lac city": "scanned Zoneomics mirror of Ch. 720 art. IV (ecode360 403)",
    "Oshkosh city": "scanned Wayback copy of city Laserfiche Ch. 30",
}
