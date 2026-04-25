# Gemini CLI Configuration - EduDisruption-Index

This project develops a data-driven Education Disruption Index (EDI) for Mali, integrating conflict (ACLED), population (WorldPop), and infrastructure (OSM) data.

## 🎯 Engineering Standards

- **Tech Stack:** Python is the primary language. Use `geopandas` for spatial operations, `pandas` for data manipulation, and `folium` or `matplotlib` for visualizations.
- **Data Integrity:** Always validate coordinate reference systems (CRS) when performing spatial joins. Use EPSG:4326 for general use and appropriate UTM zones for distance calculations.
- **Structure:**
    - `/data`: Keep raw and processed data separate.
    - `/scripts`: Modularize data cleaning, analysis, and visualization logic.
    - `/outputs`: Ensure all maps and charts are high-resolution and interpretable by non-technical stakeholders.
- **Documentation:** Every script or notebook should explain the *why* behind analytical choices (e.g., why a specific buffer distance was chosen for school accessibility).

## 🤖 Interaction Guidelines

- **Analytical Rigor:** When suggesting methods, prioritize those that address data uncertainty inherent in conflict zones.
- **Visual-First:** When generating visualization code, include interactive elements (e.g., Folium tooltips) to make the data accessible.
- **Efficiency:** Handle large datasets (like WorldPop rasters) using efficient libraries like `rasterio` or `dask` if performance becomes a bottleneck.
- **Tone:** Professional, analytical, and focused on social impact.
