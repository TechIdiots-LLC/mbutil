# MBUtil

**MBUtil** is an active, community-maintained utility for importing, exporting, and converting between the [MBTiles](https://github.com/mapbox/mbtiles-spec) and [PMTiles](https://protomaps.com/docs/pmtiles) archive formats, as well as flat directory tile structures on disk.

> [!IMPORTANT]
> This repository is a fork of the original [mapbox/mbutil](https://github.com/mapbox/mbutil), which was archived on March 10, 2026. It is now maintained under [TechIdiots LLC](https://www.techidiots.net/) and continues to be distributed under the original BSD license.

---

## ⚙️ Capabilities

- **Format Conversion**: Directly convert `.mbtiles` to `.pmtiles` and vice versa.
- **MBTiles Support**: Full import/export support for the [MBTiles](https://github.com/mapbox/mbtiles-spec) SQLite-based tile archive format.
- **PMTiles Support**: Full import/export and direct conversion support for the [PMTiles](https://github.com/protomaps/PMTiles) single-file tile archive format.
- **Disk Export**: Extract tiles from an archive to a standard directory structure (XYZ, TMS, etc.).
- **Disk Import**: Pack a directory of tiles into a single portable archive.
- **Deduplication**: Use hash-based compression to reduce file sizes for repetitive maps (e.g., oceans or vector data).

---

## 📦 Installation

This project uses git submodules for PMTiles support. The `--recursive` flag is required.

```bash
git clone --recursive https://github.com/acalcutt/mbutil.git
cd mbutil

# Install the mb-util command globally
sudo python3 setup.py install
```

> **Note:** If you already cloned the repo without submodules, run `git submodule update --init` inside the folder.

---

## 🛠 Usage

```bash
mb-util [options] <input> <output>
```

### Quick Examples

| Action | Command |
|---|---|
| Convert MBTiles to PMTiles | `mb-util world.mbtiles world.pmtiles` |
| Convert PMTiles to MBTiles | `mb-util world.pmtiles world.mbtiles` |
| Extract to Directory | `mb-util world.pmtiles ./tiles_dir` |
| Import from Directory | `mb-util ./tiles_dir world.mbtiles` |
| Dump Metadata | `mb-util world.pmtiles dumps` |

### Options

| Option | Description |
|---|---|
| `-h, --help` | Show help message and exit |
| `--scheme=SCHEME` | Tiling scheme: `xyz` (default), `tms`, `wms`, `zyx`, `ags`, `gwc` |
| `--image_format=FORMAT` | Tile format: `png`, `jpg`, `webp`, `pbf`, `mvt`, `mlt` |
| `--do_compression` | Enable hash-based tile deduplication when writing to **MBTiles** (has no effect for PMTiles or disk output) |
| `--hash_type=TYPE` | Algorithm for deduplication: `fnv1a` (fastest, default), `sha256`, `sha256_truncated`, `md5` |
| `--silent` | Disable progress logging for faster execution |

---

## 💎 Tile Deduplication

Deduplication behaviour varies by output format:

- **MBTiles output**: Use `--do_compression` to enable hash-based deduplication. Identical tiles are stored only once with internal references, which can significantly reduce file size for repetitive maps (e.g. ocean tiles, empty areas, vector data).
- **PMTiles output**: Deduplication is built into the PMTiles format and happens automatically. `--do_compression` is not needed and has no effect.
- **Disk output**: No deduplication — each tile is written as an individual file.

```bash
# Deduplicate when writing to MBTiles
mb-util --do_compression --hash_type sha256_truncated ./my_tiles world.mbtiles
```

### Hash Types

| Hash Type | Bits | Speed | Best For |
|---|---|---|---|
| **fnv1a** (default) | 64 | Fastest | General use |
| **sha256_truncated** | 64 | Medium | Balanced performance |
| **sha256** | 256 | Medium | Maximum collision resistance |
| **md5** | 128 | Fast | Legacy compatibility |

---

## ⚡ Performance & Large Files

- **Deduplication**: Use `--do_compression` when writing to MBTiles to reduce file size for repetitive content. PMTiles handles deduplication automatically.
- **Silent mode**: Use `--silent` to skip progress logging for a small speed boost.
- **Temporary Storage**: When converting to PMTiles, the utility writes a temporary file during conversion. By default this goes to `/tmp`, which on some Linux systems is RAM-backed (tmpfs). For very large files, redirect it to a physical disk:

```bash
TMPDIR=/mnt/external_drive/tmp mb-util world.mbtiles world.pmtiles
```

The temp file grows to roughly the same size as the output PMTiles archive and is deleted automatically when conversion completes.

---

## 🔗 Specifications & Resources

- [PMTiles Project](https://github.com/protomaps/PMTiles) — The cloud-native, single-file tile format.
- [PMTiles Documentation](https://protomaps.com/docs/pmtiles) — Reference for the PMTiles ecosystem.
- [MBTiles Spec](https://github.com/mapbox/mbtiles-spec) — The SQLite-based tile container specification.

---

## 🧪 Testing

Tests use Python's built-in `unittest` and are compatible with both `pytest` (recommended) and `nosetests`.

```bash
# Using pytest (recommended)
pip install pytest
pytest test/

# Using unittest directly
python -m unittest discover test/

# Using nosetests (legacy)
pip install nose
nosetests
```

Test files:
- `test/test.py` — MBTiles import/export tests
- `test/test_pmtiles.py` — PMTiles conversion and roundtrip tests (requires PMTiles submodule)

---

## 📄 License

BSD — See [LICENSE.md](LICENSE.md) for details.

---

## 👥 Authors

- **Andrew Calcutt** ([acalcutt](https://github.com/acalcutt)) — Current Maintainer
- Tom MacWright ([tmcw](https://github.com/tmcw)) — Original Creator
- Dane Springmeyer ([springmeyer](https://github.com/springmeyer))
- Mathieu Leplatre ([leplatrem](https://github.com/leplatrem))
