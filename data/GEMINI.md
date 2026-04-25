# Data Management Guidelines - EduDisruption-Index

## 📂 Structure
- `raw/`: Unmodified data directly from sources (ACLED, WorldPop, OSM).
- `processed/`: Cleaned, filtered, and joined datasets ready for analysis.

## 🛠 Standards
- **Immutability:** Never modify files in `raw/`. Always write results to `processed/`.
- **Formats:** Use `.geojson` or `.parquet` for processed spatial data to preserve types and CRS. Use `.csv` only for non-spatial tabular data.
- **Large Files:** Do not commit datasets >10MB. Use `.gitignore` and provide download scripts instead.
- **Validation:** Always check for null geometries and duplicate IDs during the cleaning phase.
