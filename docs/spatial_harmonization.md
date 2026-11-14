# Spatial harmonization

WGS84 detection centroids are transformed with pyproj to EPSG:32604 (UTM 4N), a metric WGS84 projection suitable for Maui; map geometry is exported in EPSG:4326. Hawaii's official coastline land polygon is clipped into active cells with Shapely. IDs encode resolution and floor indices in meters relative to the UTM origin. Each clipped polygon carries its projected area in square meters; coastal cells can be smaller than 1 km². Only observed cells are exported, not a full island tessellation. One centroid belongs to exactly one cell even on grid boundaries. The 1983 coastline source and its positional uncertainty remain limitations.

Scan and track are footprint dimensions, not footprint orientation. They are retained, but precise footprint polygons are not fabricated. A distance between centroids is not proof of pixel intersection or of a common incident.
