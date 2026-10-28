# EduDisruption-Index
A data-driven Education Disruption Index for Mali that combines conflict events, population distribution, and school accessibility to identify high-risk areas and support prioritisation of education interventions.


---

# 📍 Mali Education Disruption Index

## Overview

Education systems in conflict-affected regions face continuous disruption not only from direct violence, but from displacement, infrastructure damage, and reduced accessibility to schools. In Mali, these challenges are unevenly distributed across regions, making it difficult to identify where interventions are most urgently needed.

This project develops a **data-driven Education Disruption Index (EDI)** to identify areas where access to education is most at risk. The index integrates multiple indicators including conflict intensity, population distribution, and proximity to schools to provide a clearer, system-level view of education vulnerability.

---

## 🎯 Objective

The goal of this project is to support **evidence-based prioritization of education interventions** by answering a central question:

> *Where is education access most likely to be disrupted, and where should resources be focused first?*

---

## 🧠 Approach

The Education Disruption Index combines three openly available datasets:

* **Conflict events + fatalities** — ACLED (2020–2024) via HDX
* **School status** — OCHA Mali school registry via HDX
* **Population** — OCHA admin-2 estimates via HDX

These inputs are joined at the cercle level (Mali's admin-2 unit) to produce a **composite risk score** weighted **50% closures · 25% events / 100k · 25% fatalities / 100k**, plus an explicit **`data_coverage`** flag (`Full` / `Partial` / `Limited` / `Conflict-only`) so users see what evidence supports each cercle's assessment. A **`Data-Limited`** tier prevents small-N closure inflation, and a **Critical Tier** (top 5 cercles with reliable coverage) gives a defensible headline list. Full technical detail in [METHODOLOGY.md](METHODOLOGY.md).

---

## 📊 Output

The visual artifact is a two-page interactive view (the URL opens the map first; the dashboard is one click away):

* **[Map](index.html)** *(default landing page)* — choropleth of all 50 cercle boundaries coloured by tier, Critical cercles labelled, and a legend that pairs each tier with a suggested action (e.g. Critical → field-validate first); popup shows coverage, schools matched, closure rate, conflict count, fatalities, and a "what drives the score" bar splitting the EDI into its closure / events / fatalities contributions. A collapsible story panel adds a one-sentence headline answer, headline stats with sources, clickable priority-cluster cards that zoom to their cercles, a plain-language "how to read this map" note, links to the evidence (METHODOLOGY.md, SOURCES.md, pipeline), a sources list and a field-validation disclaimer
* **[Dashboard](dashboard.html)** — bubble scatter (centerpiece), donut, top-10 bar with Critical Tier highlighted in red, regional bar, "Mali at a Glance" callout, methodology note

🔗 *View the visual artifact:* [https://MegPhapha.github.io/EduDisruption-Index/](https://MegPhapha.github.io/EduDisruption-Index/)

---

## 💡 Why It Matters

In fast-changing conflict environments, decisions must often be made with incomplete information. This project demonstrates how combining open data with simple analytical methods can:

* Improve situational awareness
* Support faster and more transparent decision-making
* Complement field knowledge with system-level insights

---

## ⚠️ Scope Note

This project is a **proof-of-concept** designed for analytical clarity and adaptability. It does not replace field assessments but provides a structured way to **prioritize where deeper investigation or intervention is needed**.

---

## 📁 Repository Contents

* [PROPOSAL.md](PROPOSAL.md) – strategy section: context, objectives, approach, activities, deliverables, results
* [METHODOLOGY.md](METHODOLOGY.md) – technical reference: data sources, cleaning, EDI formula, tier rules, sensitivity check
* `/data/raw` – source files (ACLED, OCHA schools, OCHA population) with [SOURCES.md](data/raw/SOURCES.md)
* `/data/clean` – processed CSVs including `mali_disruption_summary.csv` and the 2022–2024 sensitivity comparison
* `/scripts` – `02_build_index.py` (pipeline) and `03_generate_map.py` (visualisation)
* [index.html](index.html), [dashboard.html](dashboard.html) – static HTML deployed via GitHub Pages

---

