# Sensitivity analysis

180 configurations were calculated using training and validation only. Holding grid and distance at 1,000 m, all quality, and the MODIS + S-NPP reference cohort:

| UTC tolerance (minutes) | Training candidate edges | Validation candidate edges |
|---:|---:|---:|
| 30 | 238 | 2 |
| 60 | 275 | 2 |
| 180 | 416 | 20 |
| 360 | 488 | 28 |
| 1,440 | 645 | 63 |

At 1,000 m distance / 60 min / all quality / reference cohort, changing grid from 500 to 1,000 to 2,000 m changes training active grid-cell days from 580 to 386 to 254 and validation from 77 to 50 to 42. The conservative profile retains 649 training observations and 210 links, versus 730 and 275 for all valid; validation retains 83 and 0 links versus 92 and 2. This shows scale and policy sensitivity, not accuracy. Across all tested combinations, training edges range 43–3,004 and validation 0–198; all-satellite runs include NOAA-20 with unresolved processing and are not directly comparable to the reference. Selection was not based on maximizing these counts.
