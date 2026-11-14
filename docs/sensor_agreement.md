# Descriptive agreement

Under the frozen reference, training (2013–2020) has 730 source observations, 275 candidate MODIS–VIIRS edges, 49 MODIS and 161 VIIRS observations with at least one candidate; 386 sensor-positive grid-cell days, 61 positive in both sensors, and Jaccard 61/386 = 0.158. Validation has 92 observations, 2 edges, 50 positive grid-cell days, 5 in both and Jaccard 0.10. After freeze, held-out 2023 has 324 observations, 83 edges, 135 positive grid-cell days, 25 in both and Jaccard 0.185. The holdout was not fully blinded: descriptive 2023 totals were visible during the ingestion audit before freezing.

Jaccard denominator is the union of grid-cell days with at least one detected positive from either sensor, not all observation opportunities. Candidate edges are many-to-many, and 275 edges do not mean 275 events. Unmatched observations are not false negatives. Agreement is not accuracy; no precision, recall or false-positive rate is claimed.
