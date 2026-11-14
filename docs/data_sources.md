# Data sources and limitations

- FIRMS Archive: https://firms.modaps.eosdis.nasa.gov/download/ . NASA provides CSV archive downloads; metadata must accompany the supplied data. Prefer standard science-quality products for retrospective work: https://firms.modaps.eosdis.nasa.gov/content/active_fire/ .
- MODIS FIRMS fields: https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_MODIS_Firehotspots.html . VIIRS FIRMS fields: https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html . Official VIIRS CSV example: https://firms.modaps.eosdis.nasa.gov/content/academy/data_ingest/firms_data_ingest.html . References reviewed 2026-11-14.
- NOAA-20 coverage starts 2018-04-01; NOAA-21 starts 2024-01-17, beyond the study period. Availability is not complete valid coverage. See NASA active-fire page above.
- Official Hawaii coastline: https://geodata.hawaii.gov/arcgis/rest/services/Terrestrial/MapServer/3 and https://files.hawaii.gov/dbedt/op/gis/data/coastline.pdf . A WGS84 Maui land polygon is included with a verified hash; it derives from 1983 USGS data and is not a legal survey boundary.
- MapLibre basemap: https://openfreemap.org/quick_start/ ; attribution is shown by MapLibre.
- Actual FIRMS source files, station inventory, population, roads and fire perimeters are not yet supplied. Metadata and source URLs are operator-reviewed; ingestion does not independently authenticate them.
