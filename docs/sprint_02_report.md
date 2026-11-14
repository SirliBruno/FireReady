# Sprint 02 report — implemented foundation, with outstanding requirements

## Pre-implementation audit
The existing frontend built successfully before changes. Sprint 01 had only a monthly aggregate adapter and a basemap; ingestion, observation layers and a data manager were not implemented. Its UI identity was retained. No harmonization or solver was implemented.

## Implementation
- Python ingestion discovers CSV and ZIP input, rejects unsafe ZIP member paths without extracting, recognizes MODIS/VIIRS column signatures and satellite codes, parses UTC acquisition time and Hawai‘i local time, validates fields, preserves raw records and source IDs, retains rejected and excluded rows, detects exact raw-row duplicates with lineage, applies the verified Maui coastline polygon with inclusive boundary edges when configured, and separates UTC 2013–2020 / 2021–2022 / 2023 partitions.
- Generated output includes normalized and partition Parquet, rejected and excluded Parquet, duplicate lineage, versioned manifest, data quality JSON/HTML/Markdown, sensor and temporal summaries, GeoJSON and the verified Maui coastline. Manifest and GeoJSON are checked against versioned JSON schemas. Writes use a staging directory and replacement with rollback. Outputs are isolated under `data/processed/synthetic` or `data/processed/real`.
- The manifest records source hashes, sizes, names, processing details, acquisition range, counts and limitations. The report warns of mixed processing types/versions and identifies years without accepted detections without claiming absence of fire.
- A separate `publish` command only accepts nonempty, file-error-free real-classified output after reviewer/evidence/source URL are provided; it verifies source file hashes and compares exported point positions with normalized records. Mixed processing types are blocked from publication until separated. It copies sanitized JSON/GeoJSON only. This does not authenticate NASA origin or prove scientific validity; human review is required.
- The frontend adds a Data Manager, runtime GeoJSON validation and MODIS/VIIRS map layers with visibility and point inspection when reviewed real output has been published. It does not load raw files. Harmonized layer remains unavailable. Synthetic monthly preview remains explicitly labeled and is never an automatic fallback.

## Actual verification
- Environment: Python 3.14.2, installed pinned dependencies in `.venv`; `requirements-pipeline.lock.txt` records the resolved versions.
- `python -m pytest tests/python -q`: **32 passed**. Includes UTC leading zeros, invalid times, local-day boundary, fixed partitions, official coastline edge and ocean exclusion, altered boundary hash, safe and unsafe ZIP, malformed schemas, exact duplicates and stable IDs, idempotence, source isolation, invalid manifest, tampered spatial output, mock reviewed publishing, refusal to publish mixed processing types, and physical CSV line tracing. Mock records in temporary test directories are invented.
- Full synthetic import: **8 received; 3 accepted; 2 rejected; 1 geographic exclusion; 1 temporal exclusion; 1 duplicate**. Partitions: **1 training, 1 validation, 1 test**. Parquet and GeoJSON accepted counts matched; timestamps were UTC-aware; training and held-out year ranges were checked. These are test-fixture counts only, not NASA statistics.
- Quality report was inspected. It correctly reports mixed `standard` and `NRT` and multiple processing versions for the invented fixtures. The generated no-detection years do not demonstrate no fire or complete satellite coverage.
- `npm run typecheck`, `npm run lint`, `npm test` (**9 passed**), and `npm run build` passed. Build retains a large-bundle warning (~1.81 MB JS / 511 kB gzip) and upstream Zod annotation warnings.
- Playwright: **5 targeted tests passed**, covering Data Manager awaiting data, map layer availability, mock reviewed point rendering/inspection, invalid reviewed data, and persistent synthetic labeling. Mock point data is invented in the test and never published as real.
- Data Manager and map layer controls were captured and visually inspected in no-data mode. Point selection was visually inspected with a clearly labeled synthetic test screenshot and verified in the browser using intercepted mock input; the map service requires network access.

## Commands and outputs
See `docs/data_ingestion_guide.md` for PowerShell setup and explicit reviewed publish instructions. Fixture command:

```powershell
.\.venv\Scripts\python.exe -m pipeline ingest --config config/maui.json --mode synthetic
```

Output: `data/processed/synthetic/`. Future real command uses `--mode real` and writes `data/processed/real/`. Public outputs are only copied by the separate publish command to `public/data/` after manual review. No real data was published during this sprint.

## Outstanding requirements and scientific limitations
Sprint 02 is **not fully complete** against the entire specification. The included official Maui coastline is derived from 1983 USGS data, so shore changes and positional uncertainty remain; it is not a legal survey boundary. An explicitly selected bbox-only fallback may include ocean and neighboring land. Source-specific NOAA-21 data falls outside the study window. Other valid FIRMS variants, partner-supplied files, metadata formats and source-specific edge cases have not been tested; no promise of compatibility with actual downloads is possible yet. CSV records and ZIP members are loaded into memory; large inputs/GeoJSON require streaming or tiling before operational-scale use. Published output is a single file and the Data Manager exposes a subset of quality statistics. Full coverage data is unavailable. `source_urls` require operator-supplied review metadata rather than automatic discovery. Output report timestamps intentionally vary by run even though observation IDs are stable. A full accessibility audit and visual review of every map layer were not performed. Raw path management and build performance need hardening for wider deployment.

No MODIS/VIIRS cross-sensor harmonization, incident inference, risk prediction or optimization is performed. No model calibration uses held-out 2023. All fictional fixtures are segregated and must not be presented as NASA data.

## Sources
NASA MODIS field descriptions: https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_MODIS_Firehotspots.html ; VIIRS: https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html ; product availability: https://firms.modaps.eosdis.nasa.gov/content/active_fire/ . Reviewed 2026-11-14. The Hawai‘i GIS source for the Maui-only polygon is https://geodata.hawaii.gov/arcgis/rest/services/Terrestrial/MapServer/3 ; metadata: https://files.hawaii.gov/dbedt/op/gis/data/coastline.pdf ; public-domain and no-warranty statement: https://planning.hawaii.gov/gis/download-gis-data-expanded/ .

