# Scripting Standards - EduDisruption-Index

## 💻 Development Workflow
- **Modularity:** Separate data fetching, cleaning, indexing, and mapping into distinct functions or modules.
- **Reproducibility:** Use relative paths (e.g., `../data/raw/...`) to ensure scripts run across different environments.
- **Error Handling:** Implement try-except blocks for API calls and file I/O operations.

## 📚 Preferred Libraries
- `geopandas`: Primary for spatial data.
- `pooch` or `requests`: For downloading remote datasets.
- `pyogrio`: For faster GeoPackage/GeoJSON I/O.
- `contextily`: For adding basemaps to static plots.

## 📝 Documentation
- Include docstrings for all functions specifying input types and return values (e.g., `gdf: gpd.GeoDataFrame`).
- Log major processing steps (e.g., "Filtered 1,200 conflict events for 2023").
