# EduDisruption-Index
A data-driven Education Disruption Index for Mali that combines conflict events, population distribution, and school accessibility to identify high-risk areas and support prioritisation of education interventions.


---

# 📍 Mali Education Disruption Index

## Overview

Education systems in conflict-affected regions face continuous disruption—not only from direct violence, but from displacement, infrastructure damage, and reduced accessibility to schools. In Mali, these challenges are unevenly distributed across regions, making it difficult to identify where interventions are most urgently needed.

This project develops a **data-driven Education Disruption Index (EDI)** to identify areas where access to education is most at risk. The index integrates multiple indicators—including conflict intensity, population distribution, and proximity to schools—to provide a clearer, system-level view of education vulnerability.

---

## 🎯 Objective

The goal of this project is to support **evidence-based prioritization of education interventions** by answering a central question:

> *Where is education access most likely to be disrupted, and where should resources be focused first?*

---

## 🧠 Approach

The Education Disruption Index combines three openly available datasets:

* **Conflict events** — ACLED (2020–2024) via HDX
* **School status** — OCHA Mali school registry via HDX
* **Population** — OCHA admin-2 estimates via HDX

These inputs are joined at the cercle level (Mali's admin-2 unit) to produce a **composite risk score** weighted 60% closures / 40% conflict-per-100k, plus an explicit **`data_coverage`** flag (`Full` / `Partial` / `Limited` / `Conflict-only`) so users see what evidence supports each cercle's assessment. Cercles with weak school coverage and modest conflict are routed to a **`Data-Limited`** tier instead of being mixed into the risk rankings on small-N noise.

---

## 📊 Output

The visual artifact is a two-page interactive dashboard:

* **[Map](index.html)** — one marker per cercle, sized by EDI, coloured by tier; cercles with no school-data coverage are rendered with dashed outlines
* **[Dashboard](dashboard.html)** — risk distribution, top-10 EDI cercles (Data-Limited excluded), and a **scatter chart** (conflict events per 100k vs % schools closed, by region) that visually separates cercles flagged by both signals from those flagged by only one

🔗 *View the visual artifact:* [https://megphapha.github.io/EduDisruption-Index/](https://megphapha.github.io/EduDisruption-Index/)

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

* `/data` – cleaned and processed datasets used in the analysis
* `/notebooks` or `/scripts` – code used to generate the index
* `/outputs` – maps and visualizations
* GitHub Pages site – published visual artifact

---

