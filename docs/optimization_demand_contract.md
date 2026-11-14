# Planning demand contract — final prototype

`public/data/planning/maui.json` contains aligned arrays for the browser-based hypothetical planner:

- `grid`: stable 1 km cell IDs, clipped WGS84 geometry, projected representative x/y, longitude/latitude and eligible land area in square meters.
- `monthly_weights`: keys 1–12; each vector has one nonnegative value per grid cell, in the exact `grid` order. Weight equals training local active cell-days for the month divided by eight calendar training years. Unobserved zero-weight cells remain unknown evidence, not safe land.
- `stations`: government-source professional station identifiers, names and representative geographic/projected coordinates.
- `costs_km`: row per station and column per grid cell, containing projected straight-line kilometer distances, not road travel or emergency response times.
- `model`, `model_id`, source and station limitations: provenance, cohort, UTC training partition, assumptions and dataset ID. Annual weights are the sum of all monthly vectors.

No weight equates to a required count of vehicles or personnel. Auxiliary exposure, actual operational capacity, independent event validation and observation opportunities are absent. This is a research-demand proxy usable by the included hypothetical optimizer, not an operational demand certification. See [final report](sprint_06_final_report.md).
