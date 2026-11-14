# Sprint 03 report — real-data research prototype, with outstanding work

## Inventory and ingestion
The three supplied ZIPs were copied unchanged and hashed; full inventory, sizes, original dates and SHA-256 values are in [data inventory](data_inventory.md). NASA's archive README identifies the three requested products, but source authenticity was not independently authenticated. The actual generic archive headers required a Sprint 02 parser correction: sensor identity now uses instrument metadata, full names are recognized, and the ambiguous VIIRS archive `bright_t31` is retained raw. NOAA-20 suffix-free processing is marked unknown because the [FIRMS README](https://firms.modaps.eosdis.nasa.gov/download/Readme.txt) and archive naming are not reconciled.

| Ingestion item | Actual records |
|---|---:|
| Received | 2,447 |
| Accepted within Maui polygon and UTC study period | 1,852 |
| Invalid/rejected | 0 |
| Geographic exclusions | 576 |
| Temporal exclusions | 19 |
| Exact duplicates | 0 |

Exclusions are sequential: spatial first, then temporal. Accepted satellite inventory: Terra 115, Aqua 137, S-NPP 894, NOAA-20 706. Accepted period is 2013-01-09 12:11 to 2023-12-24 11:55 UTC; source archive dates begin in 2012 and vary by product. This is not proof of uninterrupted observation coverage. Accepted partition counts: training 1,091; validation 151; test 610. Accepted FRP, confidence, scan and track are present; VIIRS archive `bright_t31` remains deliberately unmapped, so normalized I-5 is null rather than invented.

## Method, lock, and results
A pre-specified reference uses MODIS Terra/Aqua + VIIRS S-NPP, all valid native confidence, EPSG:32604 1 km cells clipped to Maui, UTC daily bins, and centroid candidate edges within 1 km / 60 minutes. It retains 1,146 observations and excludes 706 NOAA-20 observations from the reference because their processing type is unresolved. It retains 571 active cell-day units, 333 distinct active cells, 360 candidate edges and 858 observations with no candidate under the thresholds. Edges can be one-to-many; none are confirmed incident counts. Full lineage, per-sensor native attributes and FRP summaries are in outputs.

| Partition | Reference observations | Candidate edges | Active cell-days | MODIS/VIIRS positive-day Jaccard |
|---|---:|---:|---:|---:|
| Training 2013–2020 | 730 | 275 | 386 | 0.158 |
| Validation 2021–2022 | 92 | 2 | 50 | 0.100 |
| Test 2023 | 324 | 83 | 135 | 0.185 |

Jaccard is both-positive cell-days divided by the union of positive cell-days; it is descriptive agreement, not accuracy. Observation opportunities, cloud and overpass coverage are not known. The 2023 test partition was evaluated only after a write-once configuration lock, but **2023 descriptive ingestion totals were already visible during the mandatory data audit before freezing**. Thus this is not a fully blinded assessment. The reference was a priori and not chosen to maximize agreement. Lock configuration SHA-256: `3b73e239ef4dde8a4713c95a3374d2bc2d2c9377663c913ac497fab3732ea500`.

180 sensitivity configurations were computed from training and validation only. At 1 km grid, 1 km distance, all quality and reference cohort, 30/60/180/360/1,440-minute windows give training edge counts 238/275/416/488/645 and validation counts 2/2/20/28/63. For fixed 1 km and 60 minutes, 500/1,000/2,000 m grids give training active cell-days 580/386/254 and validation 77/50/42. This is parameter sensitivity, not scientific accuracy. See [sensitivity analysis](sensitivity_analysis.md) for quality profile and ranges. All-satellite scenarios contain unresolved NOAA-20 and are exploratory.

## Integration and outputs
- Core and configuration: [pipeline/harmonization.py](../pipeline/harmonization.py); the immutable local lock is `data/processed/harmonization/real/harmonization_config.lock.json`.
- Outputs are in `data/processed/harmonization/real/artifacts/`: partition activity Parquet, common grid GeoJSON, pair and unmatched Parquet, agreement and native-sensor FRP summaries, sensitivity, annual and local-month sensor summaries, manifests, JSON/Markdown report and a sanitized research preview. Source normalized and partition Parquet remain under `data/processed/real/`.
- The unreviewed local research preview is under `public/data/research/`; it is clearly labelled `real-unverified` and does not use the separate reviewed-data publication path. Raw downloads and generated artifacts are ignored by Git. User-supplied records are not synthetic, but their provenance authenticity has not been independently verified.
- Harmonization Lab displays MODIS, VIIRS and common-grid modes, UTC date and partition filters, selection details, candidate links, actual per-partition statistics, sensitivity controls, and a synchronized comparison swipe. Command Center shows the reference observation layers with an unverified label. Data Manager shows actual source counts, UTC range, satellite inventory, source filenames and exclusion counts. Synthetic mode hides real research data.

## Verification and performance
- Python tests: **44 passed**, including sensor-specific input formats, timestamps, geographic boundary, candidate one-to-many matching, unmatched observations, quality policies, lock behavior, prevention of test rows in sensitivity, and mock end-to-end partition/lineage checks.
- TypeScript check and ESLint passed; Vitest **12 passed**. Production build passed with upstream Zod annotation notices and a large JS chunk warning (about 1.84 MB / 518 kB gzip).
- Full Playwright suite: **31 passed**; after the final provenance-panel change, three targeted browser tests also passed, covering data provenance on Data Manager and Science, mobile expanded details, and synchronized comparison swipe/drag. Desktop/mobile screenshots: [grid](screenshots/sprint03-grid.png), [mobile](screenshots/sprint03-mobile.png), [comparison](screenshots/sprint03-compare.png). Data authenticity warnings remain visible. Automated and visual checks do not replace a complete accessibility audit.
- Actual-output integrity checks reconciled 1,146 reference observations, 571 cell-day rows, 360 edges, 858 unmatched observations and 333 valid positive-area clipped cells; thresholds and partition separation were checked. One local execution reported ~5.6 seconds for analysis up to, but not including, final artifact write. Sanitized preview ~1.25 MB, compact status ~5.7 KB. A single local browser run showed research readiness in ~1.6 seconds; this is not a production benchmark and external basemap availability varies.

## References and independent validation
The [official challenge page](https://www.spaceappschallenge.org/2026/challenges/harmonization-of-modis-and-viirs-hot-spots/) returned 502 to direct retrieval during this work. A description on the official Space Apps site asks for a burning-activity calendar, but its complete resource list and evaluation details could not be independently retrieved; do not invent them. Scientific rationale and primary references are in [methodology](harmonization_methodology.md): NASA FIRMS field descriptions; Schroeder et al. 2014; Li et al. 2018. Li et al.'s FRP comparison uses view-angle restrictions not available here, so only per-sensor FRP summaries are reported. USGS publishes candidate perimeter sources, including a Kula map, but no independent geospatial validation dataset has been ingested or verified. The results are descriptive cross-sensor agreement, not accuracy.

## Remaining limitations and Sprint 04 readiness
Sprint 03 is **not fully complete** against every requested feature. An independent perimeter/incident validation, observation coverage/cloud/overpass opportunities, NOAA-20 processing clarification, VIIRS archive I-5 mapping, robust chunked processing/tiling at larger scale, full map feature keyboard accessibility, separation distributions and detailed monthly/day-night agreement visualizations remain open. The comparison is a swipe overlay of synchronized maps; it does not prove footprint overlap. The current frontend only loads the fixed reference configuration; sensitivity controls display precomputed aggregate results and do not recompute maps. Configuration selection was not optimized, and the test period was not fully blinded. The polygon uses 1983 coastline data and is not a survey boundary.

Data is suitable for **exploratory descriptive seasonal analysis** with these warnings and separate held-out accounting, but not yet for validated preparedness-demand estimates, calibrated wildfire risk, operational response, or claims about the Maui disaster. Do not begin Sprint 04 automatically.

## Commands

```powershell
# Current original files are in data/raw; do not rerun ingestion over the frozen partitions casually.
.\.venv\Scripts\python.exe -m pipeline harmonize
.\.venv\Scripts\python.exe -m pipeline publish-research-preview
.\.venv\Scripts\python.exe -m pytest tests/python -q
npm run typecheck
npm run lint
npm test
npm run build
npx playwright test
npm run dev
```

Re-ingestion changes partition byte hashes because ingestion timestamps are recorded and will cause the current lock to fail. A new run would require a separately documented new freeze with disclosure of prior test exposure; do not overwrite the existing lock to hide this.
