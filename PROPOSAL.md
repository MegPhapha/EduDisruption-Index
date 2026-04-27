# Project Proposal: Mali Education Disruption Index (EDI)

**Prepared for:** Education Bridge Initiative (EBI)
**Date:** April 27, 2026
**Visual artifact:** https://megphapha.github.io/EduDisruption-Index/
**Repository:** https://github.com/megphapha/EduDisruption-Index

---

## 1. Strategy

### Context

Education systems in Mali face compounding pressure from a decade of armed conflict, mass displacement, and degraded service delivery. EBI's planning teams already know the most visible crises through their field network — but no single open dataset answers the question they need to answer next: *across the country, where is education most at risk, and where is the data we have on that risk reliable enough to act on?*

A first-pass review of the open data landscape for Mali surfaces the core problem this proposal addresses:

- **ACLED** records every conflict event but says nothing about whether schools are open. Some of the country's highest event rates per capita are in cercles where, on its own, ACLED looks like a sufficient signal — Abeibara, Tessalit, Kidal — but field teams know that "high conflict rate" in a near-empty cercle is a different decision problem than "high conflict rate" in a populated one.
- **OCHA's school registry** records facility status but covers cercles unevenly. Of Mali's 50 cercles, automated joining against the registry produces full coverage for 14, partial coverage for 9, and weak or no coverage for 27. A closure-rate ranking built on this data alone produces misleading shortlists: Bafoulabé and Kayes appear "100% closed" because only 1–2 schools matched, while Niono — with 510 conflict events — appears to have no closures at all because no schools matched.
- **WorldPop / OCHA population** estimates are reliable but are only useful in combination with the other two — population without a hazard signal is just demography.

The conclusion EBI's preliminary mapping exercise reached — that open data plus the right analytical tooling could meaningfully strengthen prioritisation — is correct. But it depends on a piece of analytical discipline that single-source maps don't provide: **knowing which cercles have enough data behind their assessment, and which are flagged on a partial signal that field teams are the only ones positioned to verify.**

### Objectives

This project delivers a composite **Education Disruption Index (EDI)** for Mali that:

1. Combines ACLED conflict events, OCHA school closure records, and population estimates into a single 0–1 score per cercle (the unit at which EBI plans).
2. Carries an explicit **`data_coverage`** flag alongside the score (`Full`, `Partial`, `Limited`, `Conflict-only`) so users see not just *what* the index says but *what evidence supports it*.
3. Produces three different but consistent shortlists from the same data:
   - The **"act now" list** — cercles where multiple signals fire and coverage is sufficient (the High tier)
   - The **"verify with field teams" list** — cercles where one signal fires hard but coverage is weak (the Data-Limited tier)
   - The **conflict-only watch list** — cercles with severe ACLED activity and no school-registry match, where field teams are the only available source of education-status information

### Proposed Approach

**Composite scoring.** Each cercle receives an EDI score combining two normalised inputs: (a) percentage of matched schools currently closed (60% weight) and (b) conflict events per 100k population over 2020–2024 (40% weight). The closure weight is higher because closure is a more direct measure of education disruption than violence rates; the conflict weight is non-zero because it captures access barriers (route safety, displacement) that closure data alone misses.

**Tiering with a data-coverage gate.** The EDI score determines a base tier (`Critical ≥ 0.7`, `High ≥ 0.4`, `Medium ≥ 0.2`, `Low < 0.2`). Cercles with weak school coverage (< 3 schools matched) and modest conflict rate (< 100 events / 100k) are routed to a **`Data-Limited`** tier instead. This prevents the small-N closure inflation that would otherwise push cercles like Bafoulabé (2 schools, both closed → "100% closed") into the High tier on noise. Cercles with weak coverage but severe conflict (e.g., Tessalit at 564/100k) keep their conflict-driven tier — because the conflict signal alone is severe enough to act on, with the coverage flag making the limitation visible.

**Visual prioritisation.** The output is a single dashboard with three connected views:

- An **interactive map** of Mali with one marker per cercle, sized by EDI, coloured by tier, and **dashed for cercles with no school-data coverage** so a glance at the map reveals not just where risk is high but where the assessment rests on a single signal.
- A **scatter chart** plotting conflict-events-per-100k against school-closure rate, with each cercle as a bubble (size ∝ √population, colour by region, hollow ring for data-gap cercles). This is the visual that supports the central argument: cercles in the upper-right are flagged by both signals; cercles isolated on one axis tell EBI which signal is driving their tier and where field verification is most needed.
- A **top-10 ranked list** that explicitly excludes Data-Limited cercles, so the headline shortlist is defensible.

### Activities

- **Data integration** — Normalise French-accented administrative names across three sources with mismatched spellings (`Baraouéli` ↔ `baraoueli`; `Niafunké` ↔ `Niafunke`); reconcile cercle codes to a single authoritative list of 50.
- **Schools matching** — Parse a non-standard multi-header XLSX from the Ministry of Education; flag cercles where automated matching yields fewer than 3 records.
- **Conflict aggregation** — Sum ACLED events per cercle for the 2020–2024 window; normalise per 100k population.
- **Composite scoring + coverage classification** — Compute EDI and assign tiers under the data-coverage rule.
- **Visualisation** — Render the map, scatter, and dashboard as static HTML with no server runtime, deployed via GitHub Pages.

### Deliverables

1. **Cleaned EDI dataset** (`mali_disruption_summary.csv`) — 50 cercles × 11 columns including the `data_coverage` flag.
2. **Interactive dashboard** with map + scatter + ranked list, designed to be read by non-technical staff.
3. **Reproducible Python pipeline** (`scripts/02_build_index.py`, `scripts/03_generate_map.py`) — under 300 lines total, using only the standard library and Chart.js / Leaflet via CDN; no proprietary dependencies.
4. **Source documentation** (`data/raw/SOURCES.md`) — provenance, licences, and known limitations of every input.

---

## 2. Use of Technology

The project uses AI not as a single feature but as a tool applied at three points where automation removes a manual bottleneck.

**AI-assisted data extraction.** The Ministry of Education school registry is distributed as a multi-sheet XLSX with three metadata rows above the header, sparse forward-fill columns, and shared-string XML internals. An LLM was used to author a custom parser for the ZIP-XML structure; the same approach generalises to other ministries' tabulations without re-engineering. For richer extraction, ACLED's free-text event notes can be processed by an LLM to flag school-related incidents (attacks, occupations, closures) that don't currently have a structured field — a near-zero-cost augmentation that materially improves signal in the closure dimension.

**AI-assisted name reconciliation.** Mali's administrative names appear with French accents, Bambara transliterations, and OCHA admin codes interchangeably. Automated string matching alone fails for 34 of 50 cercles. A combined approach — phonetic normalisation (NFKD + accent stripping) plus an LLM tie-breaker for ambiguous cases — is the practical path to closing this gap and is the single most impactful change to extend the index's coverage.

**Monitoring and scalability.** ACLED publishes weekly updates via API. A scheduled job can refresh the conflict-events column, recompute EDI, and post a short LLM-generated summary of week-over-week tier changes ("Cercle X moved from Medium to High; conflict events rose from N to M; field-team verification recommended"). This converts the EDI from a one-off exercise into a living instrument with a recurring information product field offices can subscribe to.

**Geospatial and visualisation tooling.** All analytical and visual outputs use open libraries: Python standard library for processing, Leaflet.js for the map, Chart.js for the scatter and bar/donut charts, geoBoundaries for Mali's national boundary. No proprietary licences are required. The dashboard is a single static HTML page hosted on GitHub Pages, viewable on any browser.

---

## 3. Adaptability

The methodology is built to extend without re-engineering, which is critical for an organisation operating in 12 country contexts with non-uniform data availability.

**Source-agnostic boundary.** The pipeline accepts any conflict-event source providing `(admin2_name, date)` rows, any school registry providing `(admin2_name, status)` rows, and any population source providing `(admin2_name, count)` rows. Mali demonstrates the approach on three OCHA/HDX-resident open datasets; a Yemen or DRC instantiation would swap inputs but reuse the entire processing chain.

**Data-coverage flagging as the portability mechanism.** The harder-to-port assumption isn't the data sources — it's that data quality varies. A country with strong school records and a sparse conflict reporting environment, or vice versa, will produce a different mix of tiers but the same actionable structure: `High` (act on multi-signal), `Data-Limited` (verify with field teams), `Conflict-only` watch (signal severe enough to act on a single dimension). This means the same output template serves wildly different country contexts without bespoke methodology per country.

**Scaling to changing conflict dynamics.** Because the index is recomputed from raw inputs each run, escalation in any cercle automatically moves it up the rankings — there is no static tier list to maintain. New cercles or admin-boundary changes are absorbed by updating one CSV.

---

## 4. Results Summary

Applied to Mali (2020–2024 ACLED window):

- **20 cercles ranked High** — all with Full or Partial school-data coverage. Tombouctou, Ménaka, Bourem, Bankass, and Diré lead. These are the "act now" shortlist where multiple signals fire and the assessment is well-supported.
- **22 cercles flagged Data-Limited** — including Bafoulabé and Kayes, which a closure-only ranking would have falsely placed in the top 10 on N=2 and N=1 closures respectively. Mopti town is also here, despite 336 conflict events, because only 2 schools matched. These are the "verify with field teams" shortlist.
- **4 cercles Medium, 4 Low** — backed by reliable coverage; lower priority for new resourcing.
- **The conflict-only signal alone identifies Abeibara (1,072 events / 100k), Tessalit (564), Kidal (441), and Niono (113) as needing attention** — four cercles with zero school-registry matches and severe ACLED activity, where field-team knowledge is the only available evidence on education status. The dashboard's scatter chart surfaces these as hollow rings on the right edge of the conflict axis, separating them visually from cercles where the closure signal is also driving the assessment.

The two shortlists barely overlap. A closure-only triage would have surfaced Bafoulabé, Kayes, and Banamba (all small-N, all currently flagged Data-Limited). A conflict-only triage would have surfaced Abeibara, Tessalit, Kidal, and Niono (all Conflict-only, all invisible in the schools data). Only the composite EDI surfaces both lists distinctly and tells EBI which signal is driving each cercle's tier — which is what makes it a complement to field expertise rather than a substitute for it.
