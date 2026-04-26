# Prompt Log: Mali Education Disruption Index

This file documents the sequence of requests and the project's evolution.

## 📅 2026-04-24

### 1. Initial Context & Visibility
**User:** "can you see my screen?"
**Response:** Clarified that I cannot see the physical screen but have access to the workspace files and terminal output.

### 2. Customization (GEMINI.md)
**User:** "1. Create GEMINI.md files to customize your interaction"
**Action:** Analyzed the `README.md` and RFP. Created specialized `GEMINI.md` files in the root, `/data`, `/scripts`, and `/outputs` to establish engineering and data standards.

### 3. Data Research
**User:** "I am building a data-driven Education Disruption Index for Mali. I need to combine three types of open data: conflict events, school locations, and population distribution.. What sources exist? For each, tell me what it covers, what format the data is in, and how to access it. I'm a beginner, so please use simple language."
**Response:** Identified ACLED (Conflict), OSM/HDX (Schools), and WorldPop (Population) as the primary sources, detailing their coverage, formats, and access methods.

### 4. Implementation Kickoff
**User:** "yes" (Accepting the offer to write a script for school locations).
**Action:** Researched direct download links for the Mali Schools dataset on HDX.

### 5. Data Sourcing Strategy
**User:** "I am building a data-driven Education Disruption Index for Mali... Please help me find and download the following datasets... I am a beginner working in Excel and Google Sheets."
**Response:** Provided detailed, step-by-step instructions for ACLED (Conflict), HDX (Schools), and WorldPop (Population) tailored for Excel users. Included format details, key columns, and quality flags (e.g., coordinate precision and naming inconsistencies).

### 7. Data Acquisition
**User:** "can you download the data from the links you have provided"
**Action:** Downloaded `mali_schools_2023.xlsx` and `mali_population_admin2_2020.csv`.
**User Update:** Encountered "access level" issues with ACLED's website.
**Response:** Found and downloaded the ACLED Mali mirror from HDX (`acled_mali.csv`), ensuring the user has all necessary data without login barriers.

### 9. Final Index Calculation
**User:** "Now show me exactly what the first 5 rows... Do not use Excel or VLOOKUP. Use Python with only built-in libraries..."
**Action:** Developed `scripts/02_build_index.py` using a stateful XML parser for XLSX files. Normalized all names to handle accents (e.g., 'Baraouéli' vs 'Baraoueli'). 
**Result:** Successfully generated `data/clean/mali_disruption_summary.csv` with 50 Cercles. Identified Niono, Bourem, and Koro as top high-risk areas.

### 11. Interactive Map & Publication
**User:** "i want to build a leaflet map with the data and publish it on github pages..."
**Action:** Generated `index.html` with an embedded Leaflet map. Updated `README.md` with the live link.
**Result:** Published map at [https://megphapha.github.io/EduDisruption-Index/](https://megphapha.github.io/EduDisruption-Index/)

### 12. Documentation
**User:** "create a prompt file where you document all prompts used"
**Action:** Updated `PROMPTS.md`.
