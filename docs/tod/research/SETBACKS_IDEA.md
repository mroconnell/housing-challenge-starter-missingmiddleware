# Setbacks in the lot model: idea for later

Written 2026-10-28 by the TOD conductor at the owner's request. Not started. To do after the land-value ("does it pay") step and after the current lot-model tests.

## Why

Setbacks keep buildings back from lot edges. On small or narrow lots they can stop the allowed density from physically fitting, so a rule change may not bind.

## How to code it (rough, not exact)

1. For each zoning district, take front, side and rear setbacks and lot coverage from the zoning code in force before each reform. One row per district, not per lot.
2. Each lot's width and depth come from its shape (the lot table already carries width).
3. Buildable area = (width − both side setbacks) × (depth − front − rear setbacks).
4. Buildable share = buildable area ÷ lot area, capped by the district's lot coverage limit.
5. Use it as a lot trait, and to scale the lot's homes ceiling.

## Example

| Lot | Width × depth | Setbacks (front, sides, rear) | Buildable share |
| --- | --- | --- | ---: |
| Narrow city lot | 25 × 100 ft | 15, 5 + 5, 25 ft | 36% |
| Wide lot | 60 × 120 ft | 15, 5 + 5, 25 ft | 56% |

## Work

- 9 cities, about 20–60 districts each, read from each code.
- Rules must be the ones before each reform, which makes it slower.
- Exact building envelopes are not needed and not planned.
