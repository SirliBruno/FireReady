# Sprint 04 — Historical and seasonal analysis (partial)

## Status

**Not complete.** The supplied Maui cohort was analysed and a descriptive local-calendar map was added. A defensible preparedness priority model, chronological evaluation and optimization-ready demand are not implemented. No operational allocation can be inferred. No other region has a verified configuration and input dataset. The work stops before Sprint 05.

## Inventory and data sufficiency

Three supplied archives match the SHA-256 inventory in Sprint 03. The Maui pipeline received 2,447 records, accepted 1,852 after its geographic/time filters, and retained 1,146 MODIS/Suomi NPP detections in the frozen reference cohort (252 MODIS and 894 VIIRS). NOAA-20's 706 accepted records are excluded from that reference pending resolution of processing type. Source authenticity has not been independently authenticated. Eleven local calendar years contain at least one reference detection; this does not prove continuous coverage. There are 333 distinct observed reference cells. The supplied grid contains observed cells only, including cells first seen in 2023, and cannot be treated as all eligible land or used to rank unseen cells. Cloud, overpass and observation-opportunity coverage are unavailable. Regional evidence sufficiency for operational priority is **not established**, especially at cell-month scale. No threshold was invented.

## Method and actual findings

The `analyze-seasonal` command checks the Sprint 03 preview dataset/configuration IDs against its lock and reconstructs local calendar days from individual UTC timestamps and frozen cell IDs. Distinct `(UTC partition, grid cell, local date)` groups are local observed active cell-days. UTC chronological partition labels are retained: a detection at the UTC year boundary may belong to the prior local year. Each local group retains observation IDs, sensor support and counts in `data/processed/seasonal/maui/local_cell_days.json`. This changes the day boundary only; it does not change the Sprint 03 UTC activity units. Data grouped by `(cell, local date)` had zero cross-partition collisions in this dataset.

Results: 580 local cell-days (397 training, 52 validation, 131 test), compared with 571 UTC cell-days in Sprint 03. Across all years, monthly local cell-day counts January–December are **23, 45, 8, 5, 10, 21, 136, 167, 35, 71, 35, 24**. The maximum descriptive count is August (167; 122 observed cells); July has 136. These are observations, not future fire probabilities or individual incidents, and are affected by unknown observation coverage. Training alone has 132 in July and 54 in August; 2023 test August has 105. Thus the aggregate August peak must not be described as a pre-2023 prediction. Do not infer causation, compare unadjusted years as fire incidence, or equate absence of a detection with absence of fire.

## Priority, validation, Maui case study and demand

No PPI weights, priority classes, demand weights or optimization demand dataset were fabricated. A complete eligible land grid, documented sparse-data handling and scientifically reviewed selection/evaluation strategy are still required. Unknown observation opportunities and the prior exposure of 2023 descriptive totals constrain interpretation, but do not prevent future explicitly exploratory comparisons. No held-out ranking evaluation, uniform/annual/monthly baseline comparison, sensitivity analysis or independent perimeter validation was executed in this implementation. The 2023 area is visible only as retrospective satellite observations; no conclusion about whether a pre-disaster model identified Lahaina is supported. The reference configuration was frozen before the earlier held-out analysis, but 2023 descriptive ingestion totals were already visible before that freeze, so the case cannot be called fully blinded.

No population, weather, road network, station inventory or independent wildfire perimeter is included. Geographic demand is **not ready for Sprint 05**; the included local cell-day data is descriptive research output, not a vehicle or firefighter requirement.

## Application and artifacts

The Arabic seasonal page provides Maui selection, 12 local-month buttons, local-year selection, interactive geographic cells, counts, fixed absolute legend and an explicit unknown-coverage warning. The separate legacy bar chart displays unharmonized observation counts by UTC month, which is a different unit and time basis. A year-wide selected month map is not a priority map. Insufficient/unknown coverage is not painted as low priority. Geographic feature click is available; full keyboard access to individual map cells, two-month comparison and multi-region support remain open.

Generated artifacts: `public/data/seasonal/maui.json` (229,051 bytes, SHA-256 `e108061a28de54a265f03c138b775f22ce12b35c5a9f5e937614cccc40f8cab0`); `data/processed/seasonal/maui/regional_summary.json`; and `data/processed/seasonal/maui/local_cell_days.json`. The public file retains only reference cohort observed geometries and aggregates, not the raw ZIPs. One local cold process invocation measured 0.57 seconds including Python startup; this is not a production benchmark. No region-switch or map-update latency benchmark was measured.

Run on Windows from the project root (the frozen Sprint 03 local artifacts and lock must exist):

```powershell
.\.venv\Scripts\python.exe -m pipeline analyze-seasonal --region maui --mode real
.\.venv\Scripts\python.exe -m pytest -q
npm test
npm run build
npm run lint
npx playwright test
npm run dev
```

Screenshots: [desktop](screenshots/sprint04-seasonal-desktop.png) and [mobile](screenshots/sprint04-seasonal-mobile.png). The selected month now remains visible on mobile via a 4-column layout; the mobile screenshot was refreshed after that change.

## Test results

Python: 47 passed. Vitest: 13 passed. TypeScript/production build and ESLint passed; the approximately 1.85 MB JavaScript bundle produces a size warning. Playwright: 38 passed across the full suite. Scientific tests cover local-midnight/leap-day grouping, duplicate observations per cell-day, source IDs, chronological partition boundaries and reconciliation with the available real reference. Full scientific validation, all listed missing-data/sensitivity cases, accessible map-cell navigation and independent scientific review remain outstanding.

