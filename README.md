# FireReady

FireReady is a research prototype for Maui wildfire preparedness. Satellite detections are not incidents or a forecast, and no real NASA observations are bundled. It is not an emergency warning system or NASA-endorsed product.

## Frontend

```powershell
npm install
npm run dev
```

See the Local URL printed by Vite. Real mode defaults to awaiting data. The explicitly selected synthetic preview is invented and visibly marked.

## Scientific ingestion

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-pipeline.lock.txt
.\.venv\Scripts\python.exe -m pipeline ingest --config config/maui.json --mode synthetic
.\.venv\Scripts\python.exe -m pytest tests/python -q
```

For future real inputs, place original FIRMS files under `data/raw/modis/` and `data/raw/viirs/`, then run the same ingest command with `--mode real`. Review outputs and source provenance before the separate explicit publishing command; do not replace example review URLs with invented claims. Full details: [ingestion guide](docs/data_ingestion_guide.md), [collection checklist](docs/team_data_collection_checklist.md), [data contracts](docs/data_contracts.md), and [Sprint 02 report](docs/sprint_02_report.md).

## Sprint 03 research preview

The real supplied archives were inspected and ingested locally. The browser's Harmonization Lab and Command Center may show an explicitly **unverified research preview**; provenance authenticity and independent scientific accuracy have not been established. NOAA-20 is excluded from the fixed reference cohort because its processing type is unresolved. Raw files and generated data are not committed by default. This is not a risk forecast or an operational warning system.

```powershell
# Recompute research outputs with the existing frozen lock and unchanged input partitions:
.\.venv\Scripts\python.exe -m pipeline harmonize
.\.venv\Scripts\python.exe -m pipeline publish-research-preview
npm run dev
```

The first lock was written with `python -m pipeline freeze-harmonization` and cannot be silently overwritten. Re-ingestion rewrites timestamps and partition bytes, so it invalidates the lock: retain the current files or create a separately documented new analysis and disclose that 2023 has already been viewed. `publish-research-preview` is a local research-preview export, not the separately reviewed real-data publish path. Outputs: `data/processed/harmonization/real/artifacts/`. See [Sprint 03 report](docs/sprint_03_report.md) for actual results, incomplete requirements and limitations.
