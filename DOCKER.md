# Docker Usage

The mbutil Docker image provides `mb-util` as its entrypoint. Mount a volume at `/data` containing your input file(s); output is written there as well.

## Quick Start

```bash
docker pull wifidb/mbutil
```

## Basic Conversions

```bash
# MBTiles → PMTiles
docker run -v /path/to/tiles:/data wifidb/mbutil world.mbtiles world.pmtiles

# PMTiles → MBTiles
docker run -v /path/to/tiles:/data wifidb/mbutil world.pmtiles world.mbtiles

# MBTiles → disk (tile directory)
docker run -v /path/to/tiles:/data wifidb/mbutil world.mbtiles tiles/

# Disk (tile directory) → MBTiles
docker run -v /path/to/tiles:/data wifidb/mbutil tiles/ world.mbtiles

# PMTiles → disk
docker run -v /path/to/tiles:/data wifidb/mbutil world.pmtiles tiles/

# Disk → PMTiles
docker run -v /path/to/tiles:/data wifidb/mbutil tiles/ world.pmtiles
```

## With Options

```bash
# PMTiles → MBTiles with tile deduplication
docker run -v /path/to/tiles:/data wifidb/mbutil --do_compression world.pmtiles world.mbtiles

# Dump metadata to terminal
docker run -v /path/to/tiles:/data wifidb/mbutil world.pmtiles dumps
docker run -v /path/to/tiles:/data wifidb/mbutil world.mbtiles dumps
```

## Large Files (Temp Directory)

For large conversions (multi-GB files), the PMTiles writer uses a temporary file during processing. By default this goes to `/tmp` inside the container, which is limited in-memory tmpfs. Mount a fast disk at `/tmp` to avoid running out of space:

```bash
docker run \
  -v /path/to/tiles:/data \
  -v /mnt/fast-disk/tmp:/tmp \
  wifidb/mbutil world.mbtiles world.pmtiles
```

## Input and Output in Different Directories

If your input and output are on different paths, mount them separately and use absolute paths:

```bash
docker run \
  -v /source/tiles:/source \
  -v /output/tiles:/output \
  wifidb/mbutil /source/world.mbtiles /output/world.pmtiles
```

## Specific Version

```bash
docker run -v /path/to/tiles:/data wifidb/mbutil:v0.4.0 world.mbtiles world.pmtiles
```

## Building Locally

```bash
# Initialize submodules first (required for PMTiles support)
git submodule update --init --recursive

docker build -t mbutil .
docker run -v /path/to/tiles:/data mbutil world.mbtiles world.pmtiles
```
