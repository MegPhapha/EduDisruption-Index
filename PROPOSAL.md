# Project Proposal: Mali Education Disruption Index (EDI)

**Prepared for:** Education Bridge Initiative (EBI)
**Date:** April 26, 2026

## 1. Strategy

### Context
Education systems in Mali face compounding pressures from armed conflict, displacement, and infrastructure damage. The Education Bridge Initiative (EBI) requires a system-level view to identify where interventions—such as school rehabilitation or teacher training—are most urgently needed.

### Objectives
To develop a **data-driven Education Disruption Index (EDI)** that complements field expertise with geospatial analysis, enabling EBI to prioritize resources in high-risk zones.

### Proposed Approach
The EDI is a composite score (0 to 1) calculated for each Cercle in Mali by integrating three open datasets:
1.  **Conflict Intensity:** ACLED data (2020-2024) to measure immediate security risks.
2.  **School Accessibility:** OCHA/Ministry of Education data to identify functional vs. closed facilities.
3.  **Demographic Context:** WorldPop population estimates to weigh disruption by the number of people affected.

### Activities
- **Data Integration:** Normalizing administrative names across disparate sources to ensure accurate joining.
- **Index Calculation:** Normalizing disruption and conflict metrics to a weighted 0-1 scale.
- **Geospatial Mapping:** Plotting risk tiers (Critical, High, Medium, Low) onto an interactive map for non-technical users.

### Deliverables
- **Cleaned EDI Dataset:** A CSV file containing disruption scores for all 50 Cercles.
- **Interactive Risk Map:** A Leaflet-based visualization for immediate situational awareness.
- **Reproducible Pipeline:** Modular Python scripts for future updates or adaptation to other regions.

## 2. Use of Technology

### AI and Automation
- **Complex Data Extraction:** AI tools were utilized to develop custom XML parsers capable of navigating the non-standard, multi-header structure of the raw XLSX school files.
- **Normalization:** Automation was used to apply phonetic and accent normalization to French administrative names, reducing manual cleaning time and human error.

### Geospatial Tools
- **Python (Built-in Libraries):** Used for lightweight, reproducible data processing without the need for proprietary software.
- **Leaflet.js:** An open-source mapping library used to create a "visual-first" artifact that allows field staff to hover over specific regions and see real-time statistics (School closure %, conflict events per 100k).

## 3. Results Summary
The initial analysis identified **Tombouctou, Ménaka, and Bourem** as the highest-risk areas, where school closure rates reach 100% in matched data and conflict intensity remains high.
