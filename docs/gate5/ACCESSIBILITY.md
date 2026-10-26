# Accessibility: automated checks, fixes, and the owner's screen-reader pass

Prepared 2026-10-26 after the owner's Gate 5 decision ([README.md](README.md), section 9). Tool run `adu-93c5b9a368`.

**What this is and is not.** Everything below was checked by a script in headless Chromium. That checks the structure a screen reader reads: names, roles, headings, tables, live regions and focus order. It is **not** a screen-reader pass. Nobody has yet listened to the tool with VoiceOver or NVDA; section 4 is the 20-minute checklist for that.

VoiceOver scripting was not tried. Driving VoiceOver from a script needs "Allow VoiceOver to be controlled with AppleScript" switched on in VoiceOver Utility, a system setting this session does not change.

## 1. What was checked automatically

Every screen at desktop width (1280 px), plus the Where screen switched to cities, villages and towns and to Assembly districts (11 views). Each view had all "Details" disclosures opened. The script read the browser's accessibility tree (Playwright aria snapshots) and the page, then pressed Tab 60 times to record the focus order.

| Check | Result before the fixes | Result now |
| --- | --- | --- |
| One `h1` per screen, first heading is the `h1`, no skipped levels | 11 of 11 views pass | 11 of 11 |
| Landmarks: skip link, banner, "Screens" navigation, main, footer; `lang="en"` | pass | pass |
| Every radio, checkbox, slider, search box, select, button and link has a name | pass, but the 3 scenario radios on Compare had names of 280 to 420 characters (the whole card) | names are "Lower", "Central", "Strong adoption"; the card text is the radio's description |
| Every radio group has a legend (scenario, units, areas, show, measure, unknown-rules switch) | pass | pass |
| Every table has a caption and every header cell a `scope` | pass (46 tables across the 11 views) | pass (53 tables: 7 new, 1 on Compare and 6 on the brief) |
| Charts are named images with a text summary, and each has a table with the same numbers | pass: SVG charts use `<title>` and `<desc>`; the bar strips and the sensitivity chart have `aria-label`s | pass |
| Map: named, with a keyboard route to the same values | container named; the map canvas itself was named just "Map" (MapLibre's default) | canvas says what it shows and that the table below has the same values; the table's Details buttons open each area |
| Unique ids | **fail**: `hatch-legend` repeated on 7 screens (one per chart-key swatch) | pass |
| Announcement when a switch changes the numbers | **fail**: the only live regions were inside the part of the page that is redrawn, so nothing was announced | pass: one polite status region outside the redrawn area (below) |
| Focus order | follows the page; after a switch, focus returns to the same radio; after a screen change it moves to the main content; no positive `tabindex` | same |
| Scrolling tables | Chrome made wide tables focusable without a name ("div" in the focus order) | a table wrapper that scrolls sideways becomes a named region ("…caption… (scrolls sideways)") |

Not checked automatically: colour contrast (no contrast tool is installed in this repository), reading order inside cards, how the speech actually sounds, and zoom to 200%.

## 2. What was fixed

1. **Live announcements.** A polite status region (`#announce`, outside the redrawn content) now says, for example:
   - scenario switch: "Strong adoption scenario: 16,889 permits added by the law over 2027 to 2031, 17,494 in total with the law."
   - unknown-rules switch: "Places with uncoded rules treated like places that prohibit ADUs. Over 2027 to 2031, central scenario: baseline …, added by the law …, total with the law … permits."
   - units on Compare: "Chart shows permits per 1,000 single-family homes per year."
   - Where: "Map and table: Senate districts. Permits added by statewide ADU reform (central scenario), 2027–2031. Wisconsin: 8,757."
   The year slider already announces through its `<output>`.
2. **Scenario radios** have short names and the card text as their description (number first).
3. **Unique ids** for the chart-key hatch pattern.
4. **Map canvas label** names the geography and points to the table.
5. **Scrolling tables** are named, focusable regions only when they scroll.
6. **Brief district tables** have short visible headings ("Homes", "Added", "Per 1,000/yr") and full headings for screen readers ("Added permits per 1,000 single-family homes per year"), plus a key in the text.
7. The decorative `aria-live` on the Compare tiles was removed (it was redrawn, so it never announced).

## 3. Tests that lock these in

`ui/tests/a11y.spec.ts`, run by `bash scripts/test_ui.sh` on desktop and phone:
- for each of the 11 views: one `h1`, no skipped heading levels, the four landmarks, every table captioned with scoped headers, unique ids, no positive `tabindex`, a legend on every group of radios, `lang="en"`, the live region present, and **no unnamed button, link, radio, checkbox, slider, text box, search box, combo box, image, table, region or navigation** in the accessibility tree;
- the scenario radios are named "Lower", "Central", "Strong adoption" with a description; the Where groups and the slider (`aria-valuetext` "through 2031") are named; the map canvas is labelled;
- every screen with a chart has named images and a table;
- the scenario, units, unknown-rules and Where switches each put the new numbers in the live region, and focus stays on the radio;
- the brief's district tables: 99 Assembly and 33 Senate rows, captioned, reconciled.

## 4. The owner's VoiceOver pass (about 20 minutes)

Use Safari on a Mac (VoiceOver works best with Safari). Start the tool with `bash scripts/run_tool.sh`.

**Keys.** VO = Control + Option.
| Action | Keys |
| --- | --- |
| Turn VoiceOver on or off | Command + F5 (or press Touch ID three times) |
| Read from here | VO + A; Control stops speech |
| Next / previous item | VO + Right Arrow / VO + Left Arrow |
| Rotor: headings, landmarks, links, form controls, tables | VO + U, then Left/Right Arrow to change list, Up/Down to pick, Return to go |
| Next heading | VO + Command + H |
| Next form control | VO + Command + J |
| Next table | VO + Command + T |
| Read a table: move cell by cell | VO + Arrow keys inside the table; VO + C reads the column header |
| Press a button or link | VO + Space |
| Radios | Tab to the group, then Arrow keys to change the choice |
| Open a "Details" disclosure | VO + Space on its summary |
| Move between screens | Tab through "Screens", VO + Space |

**Ten things to listen for.** Write down any "no" with the screen and what you heard.
1. **Page start.** On each screen, VO + U → Headings: is there exactly one heading level 1, and do the level-2 headings read as a sensible outline?
2. **Skip link.** First Tab on a page says "Skip to main content"; pressing it moves you to the screen's heading, not the top bar.
3. **Screen change.** Choosing a tab under "Screens" moves you to the new screen's content, and the window title names the screen.
4. **Scenario radios (Compare).** Each says "Central, radio button, 2 of 3", then the description starting with the number of added permits. The name is short, not the whole card.
5. **Announcement after a switch.** Change the scenario: within a second you hear "Strong adoption scenario: 16,889 permits added…", and focus stays on the radio. Same for the units switch and the unknown-rules switch on How sure ("Places with uncoded rules treated like…").
6. **Charts.** On a chart you hear its title and a one-sentence summary with numbers (for example "With the law in 2031: lower scenario 1,446, central scenario 2,195…"), not a list of tick labels. The table that follows has the same numbers.
7. **Tables.** In "Permits by year" and the brief's district tables, moving across a row reads the column header with each number ("Added permits per 1,000 single-family homes per year, 1.03"), and moving down reads the row header ("2029", "34").
8. **Where controls.** The groups say "Areas", "Show", "Measure", "Scenario"; the year slider says "Through year, 2031" and announces each year as you press the arrow keys; changing "Areas" announces "Map and table: …".
9. **Map and details.** The map is announced as a map of counties (or districts) that points to the table. In the table, "Details for Waukesha County" moves you to the details panel, which reads the area's name and numbers. For a city, village or town, "Back to the table" returns you to its row.
10. **Disclosures and the brief.** "Why places differ: the numbers" and other "Details" summaries say collapsed/expanded and open with VO + Space. On the brief, "Print or save as PDF" is a button, and the three Assembly tables read as "Assembly districts 1–33" etc.

**NVDA (Windows, optional).** The same ten checks with Firefox or Chrome: H next heading, D next landmark, F next form field, T next table, Control + Alt + Arrows inside a table, Insert + Down Arrow reads from here.
