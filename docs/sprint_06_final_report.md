# Sprint 06 FINAL — FireReady hackathon readiness

## Final status

A working, Arabic-first hypothetical planning demonstration is implemented for Maui: supplied FIRMS observations → source-preserving harmonization → historical/local-calendar exploration → annual or monthly train-only demand → exact station allocation → simultaneous-incident assignment. This is a bounded research/hackathon demonstration, not validated emergency dispatch. No new development sprint is proposed.

## Reproduced inputs and results

The three original ZIP hashes match the supplied source inventory. `public/data/planning/final_audit.json` records the audit. Accepted normalized rows: 1,852 from 2,447 input rows; reference cohort: 1,146 (252 MODIS and 894 Suomi NPP). NOAA-20's 706 accepted records remain excluded from the reference because processing type is unresolved. UTC reference availability: 2013-01-09T12:11:00+00:00 to 2023-12-24T11:55:00+00:00. Local training active cell-days: 397; no validation/test observations are used to construct demand. Native quality, FRP and observation lineage remain in the earlier artifacts. The original files' authenticity and scientific accuracy are not independently certified by a matching hash.

The full land grid contains 2,039 positive-area cells aligned to the frozen 1 km EPSG:32604 lattice. Ten government-sourced professional Maui station locations are used; dated eligibility/geographic assumptions and source URLs are in Sprint 05. No additional regional dataset is available, so only Maui is enabled.

The August demonstration is computed by the real solver with the monthly profile, three hypothetical vehicles, and a 10 km direct-distance threshold:

| Quantity | Geographic reference | Exact optimum |
|---|---:|---:|
| Weighted historical demand covered | 44.4% | 87.0% |
| Weighted mean direct distance | 11.38 km | 6.97 km |
| Hypothetical vehicles | 3 | 3 |

All 120 feasible three-station subsets are evaluated. Their median coverage is 61.1%, range 14.8–87.0%. These are scenario-specific coverage fractions of a historical activity proxy, not calibrated probabilities or measured emergency-response benefits. `tests/hero.unit.test.ts` independently loads actual artifacts and checks the reported rounded metrics; no result cards are hardcoded.

## Annual versus seasonal planning

Annual demand sums the twelve monthly training profiles; monthly demand uses the chosen local month. Both retain the same 2013–2020 UTC source partitions and divide positive local cell-day counts by eight calendar training years, without coverage adjustment. At 20% eligible land area, annual/monthly validation capture was 46/52 (88.5%)/37/52 (71.2%); 2023 descriptive capture was 75/131 (57.3%)/47/131 (35.9%). Annual is the default exploratory starting point for Maui because these results were already inspected. The prior 2023 exposure is disclosed; no claim of a new independent test or universal annual superiority is made. No parameters were retuned to improve the 2023 outcome.

## Allocation and simultaneous incidents

The exact subset solver maximizes weighted demand coverage, then minimizes weighted mean distance at a tie. Both reference and proposed allocations face the same budget, station set, demand and threshold. The original evenly longitude-spaced hypothetical reference is preserved. Exhaustive feasible-subset statistics contextualize it; user-configured references are not implemented.

Each selected station receives one hypothetical vehicle. Multiple vehicles at one station are not counted as extra geographic coverage. A separate exact dynamic-programming matching algorithm maximizes the number of simultaneous incidents served, then minimizes assigned direct distance, subject to each vehicle being used once and to the reachability threshold. Each incident explicitly requires one vehicle. Unreachable or resource-constrained incidents remain unserved. Up to ten hypothetical incidents can be placed near land (snapped to a cell representative within 2 km), selected by keyboard from a cell list, removed or cleared. Both deployments face identical incident locations. Assignment lines are direct geometric connections, not roads. The coverage-optimal station deployment need not outperform the reference for arbitrary user-placed incidents; the UI reports the calculated outcome.

## Arabic interface and demonstration

The simulator puts a local geographic map before simple controls and calculated result cards. Annual/monthly planning, a real-solver hero button, shared reference/proposed toggles, feasible-allocation summaries and simultaneous incidents are functional. Numeric results use bidirectional isolation. Scenario changes clear stale allocation results; incident assignments update from current inputs.

An eight-step Arabic presentation embeds real research and seasonal views and the actual simulator. Previous/next and RTL-compatible arrow navigation work. Moving from the solution to results preserves the simulator state. The rhetorical Maui hook is explicitly not a survivor quote. Official source review supports multifactorial preparedness/coordination context; no single-cause, prevention or lives-saved claim is made. No licensed historical photographs were copied without verified permissions. See `scientific_claims.md`, `hackathon_pitch_ar.md`, `hackathon_demo_guide.md`, and `judges_questions_and_answers.md`.

## Reliability, maps and performance

The simulator defaults to the included official local boundary and local processed data, with an optional external road basemap. This avoids an external tile dependency for the core solver demo. Other observation/seasonal map backgrounds still require internet, and IBM Plex Sans Arabic is now self-hosted with its SIL Open Font License and a system fallback. The local boundary is derived from older source data and is not a current legal survey. The prototype is not a service-worker offline application.

The simulator is a lazy-loaded route module. The final build still has an approximately 1.85 MB main JS chunk (about 522 kB gzip), with a small separately loaded simulator chunk; the existing map/chart dependency bundle remains a performance limitation. Research payload is 1,252,789 bytes, seasonal payload 229,051 bytes and planning payload 1,710,062 bytes. No fabricated production latency benchmark is reported. All exact solver inputs fit the ten-station MVP; exhaustive search is not proposed for large station networks.

## External verification and deployment

Road-network availability was investigated through Geofabrik's public Hawaii OSM extract listing. No road connectivity/snapping/speed validation or road-cost matrix was completed, so direct distance is used and explicitly labelled. Independent wildfire perimeter/incident validation remains unavailable in the implementation. NASA challenge title was visible in the primary search result, but the full official 2026 challenge page returned HTTP 502; deliverables/judging criteria are not certified. See `hackathon_alignment.md`.

No existing deployment target or hosting credentials are configured. The GitHub remote is source control, not a live deployment. Production build and static preview are tested locally; exact root-host and optional subpath deployment instructions are in `deployment_guide.md`. This sprint does not claim remote deployment.

## Final verification

The final executed test/build counts are appended below after the final runs. Scientific tests include exact demand reconstruction from training-only source observations, full-grid alignment, nonnegative costs, resource-budget handling, exact coverage optimum, one-vehicle/one-incident assignment, unreachable incidents and malformed inputs. Browser tests include annual/monthly selection, hero computation, zero resources, incident addition/removal, keyboard presentation, responsive layouts, route errors and production asset loading with external tiles blocked.

Screenshots: [simulator](screenshots/sprint06-simulator.png), [mobile](screenshots/sprint06-mobile.png), and `screenshots/final-{landing,command,harmonization,seasonal,resources,simulator,story,science,presentation}.png`. Actual screenshots are visually reviewed; loading-state defects found during review were fixed before final testing.

Local production demonstration:

```powershell
npm ci
npm run build
npm run preview -- --port 4185
# http://127.0.0.1:4185/#presentation
```

## Explicit readiness assessment

Ready for a local, bounded hypothetical hackathon demonstration after the passing final checks below. Not ready for operational deployment, calibrated wildfire forecasts, claims about measured response improvements, or scientifically independent 2023 validation. No new geographic region, road edges, real vehicle inventories, incident histories or economic benefits were fabricated. Team submission requirements must be checked against the official event form before submission.

### Executed final checks

- Python scientific tests: **50 passed**.
- Vitest frontend/scientific logic tests: **23 passed** (including actual artifact scenario reproduction and explicit evaluated-reference versus optimal-solver status).
- Full Playwright suite after the final application fixes: **43 passed**, with all assertions executed in one complete run. The incident illustration screenshot was additionally refreshed by one passing targeted browser run, without a subsequent application-code change.
- Production-preview Playwright test: **1 passed** against the built `dist` output on port 4185, with external tile and font endpoints blocked. Refresh, local boundary/planning assets and the actual hero solver were checked.
- TypeScript/production build and ESLint: passed. Final build main JS: 1,852.39 kB (521.50 kB gzip); lazy simulator: 17.75 kB (6.67 kB gzip). Chunk-size warning remains, with upstream Zod comment-annotation warnings.
- Four self-hosted Arabic font weights plus the original SIL OFL license are included; no remote font is required for the local demo.
- Data, route, RTL, reduced-motion, five responsive widths, keyboard presentation, zero-resource behavior, unreachable assignments and production-asset checks passed. This does not constitute a complete independent accessibility or operational scientific certification.
- Screenshots of all main views were captured and reviewed. The complete source→presentation→hero optimization journey was exercised, including preservation of simulator results between presentation steps.

[Simultaneous incidents illustration](screenshots/sprint06-incidents.png) shows actual assignments and unserved hypothetical incidents. The three-minute script is [here](hackathon_pitch_ar.md). No remote live hosting deployment is claimed; consult [deployment instructions](deployment_guide.md).
