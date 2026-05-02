# Mali EDI — Methodology

This document is the technical companion to [PROPOSAL.md](PROPOSAL.md). It records every data sourcing and cleaning decision, the EDI formula derivation, the tier and coverage classification rules, the sensitivity check, and known limitations. It documents the analytical choices behind every number that appears in the proposal, and is structured so a reviewer can re-run the pipeline and reproduce each figure cited.

## 1. Data sources

| Source | Dataset | File | Vintage | Licence |
|---|---|---|---|---|
| ACLED via HDX | Conflict events for Mali | `data/raw/acled_mali_summary.xlsx` | 2020–2024 | CC BY-NC |
| OCHA Mali via HDX | School registry (status: open/closed/destroyed) | `data/raw/mali_schools_2023.xlsx` | 2023 | CC BY |
| OCHA Mali via HDX | Admin-2 population estimates | `data/raw/mali_population_admin2_2020.csv` | 2020 | CC BY |
| geoBoundaries (wmgeolab) | Mali ADM0 polygon (national outline) | fetched at runtime by browser | 2024 | CC BY |

Full provenance and download dates also recorded in [data/raw/SOURCES.md](data/raw/SOURCES.md).

## 2. Data cleaning decisions

**Administrative-name normalisation.** Source files use French accents, Bambara transliterations, and admin codes inconsistently (e.g. `Niafunké` ↔ `Niafunke` ↔ school code `NIA042`). Implemented in `scripts/utils.py` as NFKD decomposition + accent stripping + lowercasing. Sorted matching by length-descending so longer cercle names match before substrings (e.g. `Tin-Essako` is checked before `Tin`).

**Multi-header XLSX parsing.** The OCHA school registry is distributed as XLSX with three metadata rows above the actual header and shared-string XML internals. Custom parser in `scripts/02_build_index.py` opens the ZIP archive, reads `xl/sharedStrings.xml` for string lookup, and skips rows where `r < 4`.

**ACLED sparse-row forward-fill.** The ACLED summary file uses a grouped layout where the cercle column (C) and year column (H) are populated only on the first row of each group; subsequent rows for the same cercle/year leave those cells empty. Implemented as a stateful reader: `cur_c` and `cur_y` carry forward until a new value is encountered, allowing each event-type row to inherit the correct cercle and year.

**Schools matching results.** Of Mali's 50 cercles, automated string matching against the registry produced this distribution:

| Coverage class | Count | Definition |
|---|---|---|
| Full | 14 | ≥ 10 schools matched |
| Partial | 9 | 3–9 schools matched |
| Limited | 4 | 1–2 schools matched |
| Conflict-only | 23 | 0 schools matched |

The 23 Conflict-only cercles are not a data-collection artefact (most are simply not in the regions the OCHA snapshot covered comprehensively); they are flagged in the index rather than excluded.

## 3. EDI formula

```
EDI = 0.5 × closure_rate_norm
    + 0.25 × events_per_100k_norm
    + 0.25 × fatalities_per_100k_norm
```

Each input is normalised to its dataset maximum so EDI ∈ [0, 1].

**Why these weights:**

- **Closure rate (50%).** The most direct measure of education disruption — what fraction of a cercle's known schools are not currently functional. Highest weight because it is the least proxied: it measures the outcome variable EBI cares about rather than a precondition.
- **Conflict events per 100k (25%).** Captures the access-barrier dimension that closure data alone misses: route safety, displacement, fear of attendance. Per-capita normalisation prevents densely populated cercles from dominating purely on volume.
- **Fatalities per 100k (25%).** Severity dimension. One attack with many casualties signals different urgency than many low-casualty incidents. Including fatalities prevents the index from being driven by event count alone — Tessalit (564 events / 100k, 600 fatalities / 100k) and Niono (113 / 302) illustrate the divergence.

The conflict and fatality components together carry the same weight as the closure component (50/50). This was deliberate: when closure data is reliable, it should dominate; when it isn't, the conflict + fatality pair carries the assessment.

## 4. Coverage classification

Per cercle, derived from the count of schools matched in the OCHA registry:

| Class | Rule | Mali count |
|---|---|---|
| Full | ≥ 10 matches | 14 |
| Partial | 3–9 matches | 9 |
| Limited | 1–2 matches | 4 |
| Conflict-only | 0 matches | 23 |

The four classes are designed to drive different downstream behaviour: Full and Partial cercles are eligible for the Critical Tier and Top 10 ranking; Limited and Conflict-only cercles are routed to Data-Limited unless their conflict signal is severe enough to act on alone.

## 5. Tier rules

Applied in the following order:

1. **Data-Limited.** `coverage in ('Limited', 'Conflict-only')` AND `events_per_100k < 100`. Routes weak-coverage low-conflict cercles out of the main tiers to prevent small-N closure inflation (e.g., a 1-of-1 closed school producing a misleading "100% closed" headline). 22 cercles in Mali.
2. **High / Medium / Low.** For all other cercles, applied via EDI thresholds: `≥ 0.4` High, `≥ 0.2` Medium, otherwise Low. Cercles with weak coverage but severe conflict (events / 100k ≥ 100, e.g. Abeibara, Tessalit, Kidal, Niono) keep their conflict-driven tier — the signal is strong enough to act on without closure data.
3. **Critical.** After tiering, the top 5 cercles by EDI with `coverage in ('Full', 'Partial')` are reassigned to Critical. This is a hard count, not a score threshold; it gives a defensible 5-cercle headline list regardless of where score boundaries fall.

**Mali tier breakdown (2020–2024):** Critical 5 · High 14 · Medium 4 · Low 5 · Data-Limited 22.

## 6. Sensitivity check (time window)

To test whether the EDI ranking depends on the choice of time window, the full pipeline was re-run restricting ACLED to **2022–2024 (recent half)** and compared to the **2020–2024 (full)** default.

**Critical Tier comparison:**

| Rank | 2020–2024 (full window) | 2022–2024 (recent half) |
|---|---|---|
| 1 | Ménaka (EDI 0.557) | Ménaka (EDI 0.537) |
| 2 | Tombouctou (0.532) | Tombouctou (0.530) |
| 3 | Bourem (0.522) | Bourem (0.517) |
| 4 | Bankass (0.519) | Bankass (0.514) |
| 5 | **Ansongo (0.516)** | **Diré (0.506)** |

**Stability verdict:** **4 of 5 Critical cercles are stable** across windows. The boundary swap is **Ansongo (out) ↔ Diré (in)** — Ansongo's high 2020–2021 conflict pulls it into the top 5 on the full window; Diré rises in the recent window because its closure signal is fixed (100% closed) while Ansongo's conflict drops out.

**Practical implication for EBI:** the four-cercle core (Ménaka, Tombouctou, Bourem, Bankass) is the highest-confidence triage list. The fifth slot is sensitive to which window is queried — a useful prompt for field teams, not a methodology weakness.

Sensitivity outputs are committed alongside the default outputs:
- `data/clean/mali_disruption_summary_2022_2024.csv`
- `data/clean/mali_map_data_2022_2024.csv`

The default dashboard uses the full window. To re-run the comparison: `python3 scripts/02_build_index.py` produces both files in one pass.

## 7. Known limitations

- **23 / 50 cercles have no schools-registry match.** Documented in `data/raw/SOURCES.md`. The Data-Limited tier and `coverage` flag make this transparent rather than hiding it. Closing this gap would require manual XLSX-to-CSV conversion of the source registry, which is beyond the scope of an open-data composite.
- **ACLED licence is CC BY-NC.** Reuse must be non-commercial. Acceptable for EBI's internal planning but precludes reselling the dataset.
- **No real-time refresh.** The pipeline is one-shot. ACLED publishes weekly updates via API; an automated refresh would re-aggregate and re-score on each run, but is not implemented in this prototype.
- **Mali admin boundaries are 2020 vintage.** Subsequent administrative changes (new cercles split from existing ones; renamed regions) would require updating the `pop_lookup` join and the `CAPITAL_COORDS` dictionary.
- **Closure status is a snapshot, not a time series.** The OCHA registry records current status only; no information on when a school closed or whether it has since reopened. Pairing with ACLED conflict trends partially mitigates this but does not replace longitudinal school data.
- **Fatality counts in ACLED are widely accepted to be conservative.** Under-reporting is more likely in cercles with weaker observer presence. The same cercles where school data is also sparse. The fatalities weight should be read as a relative severity signal, not an absolute casualty estimate.
