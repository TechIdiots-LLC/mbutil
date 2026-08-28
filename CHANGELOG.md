# Changelog

## master
### ✨ Features and improvements
- _...Add new stuff here..._

### 🐞 Bug fixes
- _...Add new stuff here..._

## 0.4.6
### ✨ Features and improvements
- Add MLT (MapLibre Tile) as a supported `--image_format` (@acalcutt)
- Publish to PyPI as `pmtiles-mbtiles-util` (@acalcutt)
- Depend on the `pmtiles` package, so PMTiles conversion works in an installed copy and not only in a source checkout, and drop the PMTiles git submodule (@acalcutt)
- Install `mb-util` as a console script entry point, so pip creates a launcher and the command works on Windows (@acalcutt)

### 🐞 Bug fixes
- Export tiles using the format declared in the archive metadata rather than always `.png`, so MBTiles→disk gives `.pbf`/`.mlt` tiles the right extension without passing `--image_format` (@acalcutt)
- Set the PMTiles tile type for formats the bundled PMTiles library does not map, so MBTiles→PMTiles no longer writes `Unknown` for MLT (@acalcutt)
- Fold the MLT media type (`application/vnd.maplibre-vector-tile`, written by Planetiler) to `mlt` when reading metadata, so such archives convert instead of crashing on the `/` in the tile extension or landing in PMTiles as `Unknown` (@acalcutt)

## 0.4.5
### ✨ Features and improvements
- Update PMTiles ([#12](https://github.com/TechIdiots-LLC/pmtiles-mbtiles-util/pull/12)) (@acalcutt)

## 0.4.4
### 🐞 Bug fixes
- Use format as a falback for tile type ([#10](https://github.com/TechIdiots-LLC/pmtiles-mbtiles-util/pull/10)) (@acalcutt)

## 0.4.3
### 🐞 Bug fixes
- make sure pbf/mvt are gzipped ([#8](https://github.com/TechIdiots-LLC/pmtiles-mbtiles-util/pull/8)) (@acalcutt)

## 0.4.2
### ✨ Features and improvements
- Read format from metadata ([#6](https://github.com/TechIdiots-LLC/pmtiles-mbtiles-util/pull/6)) (by [acalcutt](https://github.com/acalcutt))

## 0.4.1
### ✨ Features and improvements
- Update MBUtil description in README.md ([#4](https://github.com/TechIdiots-LLC/pmtiles-mbtiles-util/pull/4)) (by [acalcutt](https://github.com/acalcutt))
- Add message if file does not exist.

## 0.4.0

### Added
- **PMTiles ↔ Disk**: Export tiles from a `.pmtiles` file to a folder structure, or import a tile folder into a new `.pmtiles` file (`disk_to_pmtiles`, `pmtiles_to_disk`).
- **MBTiles ↔ PMTiles direct conversion**: Convert between `.mbtiles` and `.pmtiles` without an intermediate disk step (`mbtiles_to_pmtiles_cmd`, `pmtiles_to_mbtiles_cmd`). Detected automatically by file extension.
- **PMTiles metadata dump**: `mb-util archive.pmtiles dumps` prints metadata to the terminal.
- **Tile deduplication on PMTiles→MBTiles**: `--do_compression` and `--hash_type` flags work when converting PMTiles to MBTiles.
- Metadata helpers: `normalize_metadata()`, `prepare_metadata_for_mbtiles()`, `get_tile_ext()`, `pmtiles_header_to_metadata()`.
- PMTiles reference Python library included as a git submodule.
- Full unit test suite (`test/test_pmtiles.py`) and GitHub Actions CI workflow.
- Docker image with multi-arch support (amd64, arm64).

### Fixed
- Y-coordinate flipping between TMS (MBTiles) and XYZ (PMTiles) coordinates.
- Out-of-bounds tile IDs are skipped with a warning instead of crashing.
- `scheme` metadata key removed when writing PMTiles output; `scheme: tms` added when writing MBTiles output.
- Center zoom fallback to `(min_zoom + max_zoom) // 2` when value is missing or zero.
- Graceful `NotImplementedError` when PMTiles submodule is not initialized.
- Vector tiles (PBF) are gzip-compressed when writing to PMTiles if not already compressed.
- `json` metadata row (`vector_layers`, `tilestats`) correctly round-trips between MBTiles and PMTiles formats.
- `optimize_database` connection not closed after PMTiles→MBTiles conversion (caused "database is locked" errors).

## 0.3.0

- Initial public release with MBTiles import/export support.
