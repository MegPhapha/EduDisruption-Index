# Project Proposal: Mali Education Disruption Index (EDI)

**Prepared for:** Education Bridge Initiative (EBI)
**Date:** April 27, 2026
**Visual artifact:** https://megphapha.github.io/EduDisruption-Index/
**Repository:** https://github.com/MegPhapha/EduDisruption-Index
**Technical reference:** [METHODOLOGY.md](METHODOLOGY.md)

---

## 1. Strategy

### Context

Education systems in Mali face compounding pressure from a decade of armed conflict, mass displacement, and degraded service delivery. EBI's planning teams already know the most visible crises through their field network — but no single open dataset answers the question they need to answer next: *across the country, where is education most at risk, and where is the data we have on that risk reliable enough to act on?*

A first-pass review of the open data landscape for Mali surfaces the core problem this proposal addresses:

- **ACLED** records every conflict event but says nothing about whether schools are open. Some of the country's highest event rates per capita are in cercles where, on its own, ACLED looks like a sufficient signal — Abeibara, Tessalit, Kidal — but field teams know that "high conflict rate" in a near-empty cercle is a different decision problem than "high conflict rate" in a populated one.
- **OCHA's school registry** records facility status but covers cercles unevenly. Of Mali's 50 cercles, automated joining produces full coverage for 14, partial for 9, and weak or no coverage for 27. A closure-rate ranking built on this data alone would falsely place Bafoulabé and Kayes in the top 10 (N=2 and N=1 schools matched, both 100% closed), while Niono — with 510 conflict events — would appear to have no closures because no schools matched at all.
- **WorldPop / OCHA population** estimates are reliable but only useful in combination with the other two — population without a hazard signal is just demography.

The conclusion EBI's preliminary mapping exercise reached — that open data plus the right analytical tooling could meaningfully strengthen prioritisation — is correct. But it depends on a piece of analytical discipline that single-source maps don't provide: **knowing which cercles have enough data behind their assessment, and which are flagged on a partial signal that field teams are the only ones positioned to verify.**

### Objectives

This project delivers a composite **Education Disruption Index (EDI)** for Mali that:

1. Combines ACLED conflict events, ACLED fatalities, OCHA school closure records, and population estimates into a single 0–1 score per cercle (the unit at which EBI plans).
2. Carries an explicit **`data_coverage`** flag alongside the score (`Full`, `Partial`, `Limited`, `Conflict-only`) so users see not just *what* the index says but *what evidence supports it*.
3. Surfaces three different but consistent shortlists from the same data:
   - The **Critical Tier** — top 5 cercles with reliable coverage; the act-now list
   - The **Data-Limited** flag — cercles where one signal fires hard but coverage is weak; the verify-with-field-teams list
   - The **Conflict-only watch list** — cercles with severe ACLED activity and no school-registry match, where field teams are the only available source of education-status information

### Proposed Approach

**Composite scoring.** EDI = 0.5 × closure-rate + 0.25 × events / 100k + 0.25 × fatalities / 100k. Each input normalised to its dataset maximum so EDI ∈ [0, 1]. Closure rate carries the highest weight because it is the most direct measure of education disruption rather than a precondition. Events and fatalities together carry the same weight (50/50): events capture *frequency* of insecurity, fatalities capture *severity*. Including both prevents the index from being driven by event count alone, where a single high-casualty attack would otherwise weigh the same as a brief skirmish.

**Tiering with a data-coverage gate.** Cercles with weak school coverage (< 3 schools matched) AND modest conflict rate (< 100 events / 100k) are routed to a **`Data-Limited`** tier instead of being scored against the main thresholds. This prevents small-N closure inflation. Cercles with weak coverage but severe conflict (e.g., Tessalit at 564 events / 100k) keep their conflict-driven tier — the signal alone is severe enough to act on, with the coverage flag making the limitation visible.

**Critical Tier.** After tiering, the top 5 cercles by EDI with `coverage in ('Full', 'Partial')` are reassigned to Critical. Hard-coded count, not a score threshold; gives a defensible 5-cercle headline list regardless of where score boundaries fall.

**Visual prioritisation.** The output is a single dashboard plus a separate full-screen map:

- A **bubble scatter** (centerpiece of the dashboard) plotting conflict events per 100k against school-closure rate, with each cercle as one bubble. Size scales with √population, colour marks the region, and **hollow rings** flag cercles where school-data coverage is too thin for the closure signal to be trusted.
- A **donut, top-10 bar (Critical bars in dark red), and regional bar** alongside the scatter, plus a "Mali at a Glance" callout summarising the headline numbers (5 Critical cercles, 22 Data-Limited, top cercle, top region).
- A separate **full-screen interactive map** with one marker per cercle, sized by EDI and coloured by tier (grey markers = Data-Limited cercles where the assessment rests on the conflict signal alone). Clicking a cercle surfaces its coverage, schools matched, closure rate, conflict count, and fatality count.

**Reading the bubble chart.** The scatter is built so that each cercle's *position* on the chart names its risk profile:

- **Upper-right (filled bubbles)** — both signals fire. The Critical Tier sits here.
- **Upper-left (filled)** — closures without much conflict; in Mali these are mostly small-N artifacts and route to Data-Limited.
- **Right edge (hollow rings)** — severe conflict, no school-registry match (Abeibara, Tessalit, Kidal, Niono). The conflict-only watch list.
- **Lower-left** — low on both signals. No urgent action.

If conflict and closures tracked the same cercles, the bubbles would form a diagonal. They form an **L-shape** instead, with hollow rings stretching along the right edge and filled bubbles climbing through the middle. That gap is the methodology argument made visually: a single-source ranking would surface the wrong cercles, but the composite EDI with explicit coverage flags surfaces both shortlists distinctly.

A **top-10 ranked list** sits beside the scatter and explicitly excludes Data-Limited cercles. Critical Tier cercles in this list are bar-coloured red; the rest navy.

See [METHODOLOGY.md](METHODOLOGY.md) for full technical detail on data cleaning, weight derivation, coverage thresholds, tier rules, the sensitivity check, and known limitations.

### Activities

- **Data integration** — Normalise French-accented administrative names across three sources with mismatched spellings (`Baraouéli` ↔ `baraoueli`; `Niafunké` ↔ `Niafunke`); reconcile cercle codes to a single authoritative list of 50.
- **Schools matching** — Parse a non-standard multi-header XLSX from the Ministry of Education; classify each cercle's coverage (Full / Partial / Limited / Conflict-only).
- **Conflict aggregation** — Sum ACLED events and fatalities per cercle for the 2020–2024 window; normalise per 100k population.
- **Composite scoring + Critical Tier assignment** — Compute EDI under the 50/25/25 weighting, apply the Data-Limited gate, then reassign the top 5 reliable cercles to Critical.
- **Sensitivity check** — Re-run the full pipeline restricted to 2022–2024 (recent half) to test the ranking's stability across time windows.
- **Visualisation** — Render the dashboard and map as static HTML with no server runtime, deployed via GitHub Pages.

### Deliverables

1. **Cleaned EDI dataset** (`data/clean/mali_disruption_summary.csv`) — 50 cercles × 13 columns including the `data_coverage` flag, fatalities, and risk tier.
2. **Sensitivity comparison dataset** (`data/clean/*_2022_2024.csv`) — same schema, restricted to recent half.
3. **Interactive dashboard** with bubble scatter as the centerpiece, plus donut, top-10 bar (Critical highlighted), regional bar, "Mali at a Glance" callout, and methodology note. Single-screen layout designed to be read by non-technical staff.
4. **Full-screen interactive map** linked from the dashboard.
5. **Reproducible Python pipeline** (`scripts/02_build_index.py`, `scripts/03_generate_map.py`) — using only the standard library and Chart.js / Leaflet via CDN. No proprietary dependencies.
6. **Technical methodology reference** ([METHODOLOGY.md](METHODOLOGY.md)) — data sourcing, cleaning decisions, formula derivation, tier rules, sensitivity check, and known limitations.

---

## 2. Use of Technology

The project uses AI as a code-and-prose accelerator with all analytical decisions made by a human reviewer. The boundary is explicit:

**AI-led work**

- Generation of the custom XLSX parser for the multi-header school registry (ZIP-XML structure with shared strings)
- Generation of the ACLED sparse-row forward-fill code for the grouped-layout summary file
- Authoring of the French/Bambara/admin-code name normalisation logic (NFKD + accent stripping + length-descending substring match)
- Drafting of the dashboard HTML/CSS scaffold and Chart.js configuration boilerplate
- Authoring weight-shift sensitivity test scripts (the implementation that produced the 2022–2024 comparison)
- Initial drafts of proposal and methodology copy, subsequently rewritten by hand

**Human-led decisions**

- The 50 / 25 / 25 weighting (closure / events / fatalities)
- The Critical Tier definition (top 5 with reliable coverage, not a score threshold) — chosen to give a hard-count headline list
- The Data-Limited gate threshold (events / 100k < 100) and the carve-out for severe conflict
- Coverage classification thresholds (Full ≥ 10, Partial 3–9, Limited 1–2, Conflict-only 0)
- Visual prioritisation choices — scatter as centerpiece, what to surface in popups, when to use hollow rings vs solid markers, dashboard layout
- Sources audit and licence verification (including catching that ACLED is CC BY-NC, not CC BY)
- The angle and rhetorical framing of the proposal, two-cercle contrast paragraph, and methodology section structure

**Monitoring and scalability.** ACLED publishes weekly updates via API. A scheduled job can refresh the conflict-events and fatalities columns, recompute EDI, and post a short LLM-generated summary of week-over-week tier changes ("Cercle X moved from Medium to High; conflict events rose from N to M; field-team verification recommended"). This converts the EDI from a one-off exercise into a living instrument with a recurring information product field offices can subscribe to.

**Tooling.** All analytical and visual outputs use open libraries: Python standard library for processing, Leaflet.js for the map, Chart.js for the scatter and bar/donut charts, geoBoundaries for Mali's national boundary. No proprietary licences are required. The dashboard is a single static HTML page hosted on GitHub Pages, viewable on any browser.

---

## 3. Adaptability

The methodology is built to extend without re-engineering, which is critical for an organisation operating in 12 country contexts with non-uniform data availability.

**Source-agnostic boundary.** The pipeline accepts any conflict-event source providing `(admin2_name, date, fatalities)` rows, any school registry providing `(admin2_name, status)` rows, and any population source providing `(admin2_name, count)` rows. Mali demonstrates the approach on three OCHA/HDX-resident open datasets; a Yemen or DRC instantiation would swap inputs but reuse the entire processing chain.

**Data-coverage flagging as the portability mechanism.** The harder-to-port assumption isn't the data sources — it's that data quality varies. A country with strong school records and a sparse conflict reporting environment (or vice versa) will produce a different mix of tiers but the same actionable structure: Critical (act on multi-signal with reliable data), High / Medium / Low (graded by EDI with reliable coverage), Data-Limited (verify with field teams), Conflict-only watch (signal severe enough to act on a single dimension). The same output template serves wildly different country contexts without bespoke methodology per country.

**Scaling to changing conflict dynamics.** Because the index is recomputed from raw inputs each run, escalation in any cercle automatically moves it up the rankings — there is no static tier list to maintain. The sensitivity check (2020–2024 vs 2022–2024) demonstrates that the four-cercle core of Mali's Critical Tier (Ménaka, Tombouctou, Bourem, Bankass) is stable across time windows; the fifth slot is sensitive to the window choice — useful intelligence for field teams, not a methodology weakness.

---

## 4. Results Summary

Applied to Mali (2020–2024 ACLED window), the EDI surfaces a clear five-cercle act-now shortlist:

**Critical Tier — the 5 cercles requiring immediate assessment:**

| Rank | Cercle | Region | EDI | Closure | Events / 100k | Fatalities / 100k | Coverage |
|---|---|---|---|---|---|---|---|
| 1 | **Ménaka** | Gao | 0.557 | 80% | 430.6 | 1,548.0 | Full |
| 2 | **Tombouctou** | Tombouctou | 0.532 | 100% | 118.5 | 129.4 | Full |
| 3 | **Bourem** | Gao | 0.522 | 100% | 62.1 | 206.4 | Partial |
| 4 | **Bankass** | Mopti | 0.519 | 96.7% | 95.9 | 358.5 | Full |
| 5 | **Ansongo** | Gao | 0.516 | 80% | 312.4 | 1,171.3 | Partial |

These are the only cercles where the index has both reliable school-data coverage *and* a top-five EDI score. Three of the five are in Gao region, suggesting regional concentration of the highest-confidence risk signal that EBI can defend to a programme officer without further caveat.

**Tombouctou vs Abeibara — two kinds of risk that a single-source ranking would conflate.** The composite reveals two distinct profiles. **Tombouctou** (Critical Tier #2) sits in the upper-right of the bubble chart with a closure-driven EDI: 11 of 11 matched schools closed, 186 conflict events over 5 years, 203 fatalities, full school-data coverage backing the assessment. **Abeibara**, by contrast, is a hollow ring on the right edge — zero schools registered in the OCHA file, but **1,072 ACLED events per 100,000 people** (the highest rate in Mali) and 868 fatalities. Tombouctou ranks Critical because both signals fire and the data is reliable; Abeibara ranks High purely on conflict severity, and only because the methodology preserves its score when coverage is weak but the conflict signal is overwhelming. The two cercles need different responses (infrastructure rehabilitation in Tombouctou; safety-driven access intervention in Abeibara) and different verification (data-confirmed vs. field-team confirmed). Only the composite EDI with explicit coverage flagging surfaces both as urgent while flagging the difference between them.

**Tier breakdown:** 5 Critical · 14 High · 4 Medium · 5 Low · 22 Data-Limited.

**Conflict-only watch list (no school-registry match, severe ACLED):** Abeibara (1,072 events / 100k), Tessalit (564), Kidal (441), and Niono (113). Together these four cercles cover ~520,000 people for whom the closure axis tells us nothing and field-team knowledge is the only available evidence.

**Two shortlists, barely overlapping.** A closure-only triage would have surfaced Bafoulabé, Kayes, and Banamba (all small-N, all currently flagged Data-Limited and excluded from the Critical Tier). A conflict-only triage would have surfaced Abeibara, Tessalit, Kidal, and Niono (all Conflict-only, all invisible in the schools data). Only the composite EDI with the data-coverage gate produces a defensible Critical Tier *and* a Conflict-only watch list distinctly — which is what makes it a complement to field expertise rather than a substitute for it.

**Sensitivity check.** Re-running the full pipeline restricted to 2022–2024 produces a Critical Tier with 4 of 5 cercles unchanged (Ménaka, Tombouctou, Bourem, Bankass). The fifth slot swaps Ansongo (out) for Diré (in), reflecting that Ansongo's 2020–2021 conflict load exits the window. The four-cercle core is the highest-confidence triage list across both windows. See [METHODOLOGY.md §6](METHODOLOGY.md) for the comparison table.
