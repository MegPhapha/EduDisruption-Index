# Raw Data Sources

## 1. Mali Schools (mali_schools_2023.xlsx)
- Source: OCHA Mali via HDX
- URL: https://data.humdata.org/dataset/mali-schools
- Downloaded: April 2026
- Rows: 9,143
- Format: XLSX
- License: Creative Commons Attribution

## 2. Conflict Data (acled_mali_summary.xlsx)
- Source: ACLED via HDX
- URL: https://data.humdata.org/dataset/acled-data-for-mali
- Downloaded: April 2026
- Rows: 278 (aggregated by cercle/month/event type)
- Format: XLSX
- License: Creative Commons Attribution Non-Commercial

## 3. Population Data (mali_population_admin2_2020.csv)
- Source: OCHA Mali via HDX
- URL: https://data.humdata.org/dataset/mali-subnational-population
- Downloaded: April 2026
- Rows: 50 (one per cercle)
- Format: CSV
- License: Creative Commons Attribution

## Notes on data quality
- Region and cercle names are in French throughout
- Accent normalisation was applied during cleaning
  to ensure consistent joins across files
  (e.g. "Baraouéli" → "baraoueli")
- Schools file contained 3 metadata rows at the top
  which were skipped during processing
- ACLED file uses sparse/grouped row format;
  a stateful reader was used to forward-fill
  cercle and year values

## Data Limitation — School Matching

The mali_schools_2023.xlsx file uses a complex 
multi-header structure with school codes that 
partially resemble cercle names (e.g. "NarA4738").
This caused unreliable automated matching.

School counts in the EDI reflect only cercles where 
matching was unambiguous (16 of 50 cercles).
For remaining cercles, EDI is based on conflict 
intensity only. Full school integration would 
require converting the raw XLSX to a flat CSV 
with explicit cercle columns.
