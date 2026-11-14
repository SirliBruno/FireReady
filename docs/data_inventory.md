# Data inventory — observed 2026-11-14

The three user-supplied ZIP files were copied unchanged into `data/raw/`; source authenticity has not been independently authenticated. NASA FIRMS [archive README](https://firms.modaps.eosdis.nasa.gov/download/Readme.txt) identifies M-C61 as MODIS, SV-C2 as S-NPP VIIRS, and J1V-C2 as NOAA-20 VIIRS. These are thermal detections, not distinct fires.

| Archive | Bytes | SHA-256 | Original rows | Original acquisition dates | Satellites |
|---|---:|---|---:|---|---|
| DL_FIRE_M-C61_847409.zip | 6,913 | a0945bc906f786f725bcc9e8afe79ddddc0fe25b902db4c96af218282244087a | 313 | 2012-05-05–2023-12-13 | Terra, Aqua |
| DL_FIRE_SV-C2_847363.zip | 21,612 | 6959a18687b147b1a00e5becf02eec124cf008f385a22688db4a39466a778cb0 | 1,189 | 2012-03-11–2023-12-24 | Suomi NPP |
| DL_FIRE_J1V-C2_847420.zip | 16,936 | a6dc515d90231d8fecb204e9040eab7163c7e9ee1d3ad9231287599c1f7966e0 | 945 | 2018-05-19–2023-10-23 | NOAA-20 |

2,447 input rows: 1,852 accepted; zero rejected; 576 spatial exclusions, 19 temporal exclusions, zero exact duplicates. Exclusions are sequential (spatial before temporal). Accepted satellite counts: Terra 115, Aqua 137, S-NPP 894, NOAA-20 706. Accepted UTC extent: 2013-01-09 12:11 through 2023-12-24 11:55. UTC partitions: training 1,091; validation 151; test 610. Accepted observation coordinates span [-156.68788,20.5813,-155.98647,21.01811]. These endpoints and gaps do not establish observation opportunity or continuous coverage.

The archive uses shared brightness column names and `SNPP` or full MODIS satellite names. Sensor metadata now resolves these signatures; NASA documents VIIRS `brightness` as I-4 in web services. VIIRS `bright_t31` is preserved raw and not asserted to be I-5 until its archive mapping is independently confirmed. All accepted rows have FRP, native confidence, scan and track, but the VIIRS I-5 normalized column is intentionally null. Versions: MODIS `6.03` and `61.03`, VIIRS `2`. NOAA-20 processing type remains unknown: archive naming and the current NASA README's standard-product statement are not reconciled. Reference cohort excludes it; all-cohort sensitivity is exploratory only.
