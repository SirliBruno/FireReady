# Ingestion guide

PowerShell on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-pipeline.lock.txt
.\.venv\Scripts\python.exe -m pipeline ingest --config config/maui.json --mode synthetic
.\.venv\Scripts\python.exe -m pytest tests/python -q
```

The fixture path is `data/fixtures/firms` and outputs are written to `data/processed/synthetic`. The inputs are invented examples, not NASA records. Never publish them as real.

When the teammate supplies original files, place them under `data/raw/modis` and `data/raw/viirs` without modifying the originals. Run:

```powershell
.\.venv\Scripts\python.exe -m pipeline ingest --config config/maui.json --mode real
```

Inspect `data/processed/real/dataset_manifest.json`, `data_quality_report.md`, rejected and excluded records, source hashes, warnings, and partition counts. Obtain source URLs and perform independent scientific and provenance review. To publish only reviewed real output locally, explicitly run:

```powershell
.\.venv\Scripts\python.exe -m pipeline publish --reviewer "Name" --evidence "https://example.org/review" --source-url "https://example.org/source"
```

Replace the examples with actual review and source links. This is a local copy to `public/data`, not a remote deployment. The publish command checks original raw file hashes, rejects synthetic, empty, file-error and mixed-processing-type outputs; it sets status last and never copies raw source records. Review fields are assertions, not verification of source authenticity. `--mode real` alone does not validate origin. This initial implementation recognizes particular documented FIRMS CSV signatures, not every possible NASA export. Inspect actual downloads before relying on compatibility.


The default configuration uses the bundled Hawaii State GIS Maui coastline. If its configured file is missing or its hash does not match the reviewed copy, the import fails. Removing `boundary_path` opts into a clearly labeled provisional bounding-box-only workflow.
