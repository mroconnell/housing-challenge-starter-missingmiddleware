// The "How we count" line for each reform: one source for the Introduction's ranges table and every reform's Summary
// tab, so the two can never drift apart. Owner-approved copy (Claude Doc rev 180, audit-cleared); the order is fixed:
// ADUs, Middle housing, TOD, Parking.
export type ReformKey = "adu" | "middle" | "tod" | "parking";
export const REFORM_ORDER: ReformKey[] = ["adu", "middle", "tod", "parking"];

export const HOW_WE_COUNT: Record<ReformKey, string> = {
  adu: "ADU permits. We learned the ADU rate once a statewide law is in force from 8 states (plus 5 cities), adjusting for home values and incomes. We hid 7 of the states one at a time and predicted each from the rest: predictions ran from 12% too low to 21% too high. The range is set from the size of those misses.",
  middle: "Homes in 2–4 unit buildings. We measured how these homes changed in the 4 states with statewide middle housing laws, each against similar places in its own region, and did the same for 10,000 groups of 4 states without a law. The reform states beat 85 of every 100 groups, short of the 95 needed to call it clear. So Wisconsin's range still includes zero: the evidence can't tell yet whether the law changes the number of these homes.",
  tod: "Extra homes permitted near transit. We compared permits within ¼ mile of rail and rapid-bus stops in 11 places that adopted upzoning near transit. In each place, we found some stops with an upzoned apartment district nearby, and other similar stops that weren't rezoned, mostly in the same city. We looked at permits before and after the reforms, across both kinds of stops. The whole range is above zero, so the evidence points to extra homes permitted.",
  parking: "Homes. We studied 74 places that repealed parking minimums for housing, each compared with similar cities that kept them, and ran fake repeals in 9,185 cities that never repealed. A range that includes zero means the data can't tell whether repealing parking minimums alone adds or removes homes.",
};
