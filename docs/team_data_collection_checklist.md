# Team data collection checklist

- Study window: 2013-01-01 through 2023-12-31 UTC. Approximate bounding box: west -156.75, south 20.55, east -155.95, north 21.10. The rectangle is preliminary; the pipeline also applies the included Maui-only official coastline polygon by default.
- Request MODIS Terra and Aqua, VIIRS Suomi NPP and NOAA-20 where available. NOAA-20 starts in 2018; NOAA-21 starts in 2024 and is outside the study window.
- Prefer FIRMS Archive standard science-quality CSV, retaining all original fields. ZIP archives are acceptable. Do not preprocess or drop fields.
- Preserve source download URL, product, acquisition range, retrieval date, processing collection/version and any metadata. File names alone do not prove processing or source identity.
- Place MODIS files in `data/raw/modis/`, VIIRS in `data/raw/viirs/`, and auxiliary files in `data/raw/auxiliary/`. Do not overwrite original downloads.
- Optional: an independently verified newer Maui coastline, roads, station locations, historical fire perimeters and population exposure, with metadata, time coverage and usage rights.
- Detections are not incidents; no detection is not proof of no fire. Provide metadata separately when not in the CSV.
