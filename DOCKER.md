# Docker Usage

The `techidiotsllc/pmtiles-mbtiles-util` image provides `pmtiles-mbtiles-util` as its entrypoint. Mount a volume at `/data` containing your input file(s); output is written there as well.

## Quick Start

```bash
docker pull techidiotsllc/pmtiles-mbtiles-util
```

## Basic Conversions

```bash
# MBTiles → PMTiles
docker run -v $(pwd):/data techidiotsllc/pmtiles-mbtiles-util world.mbtiles world.pmtiles

# PMTiles → MBTiles
docker run -v $(pwd):/data techidiotsllc/pmtiles-mbtiles-util world.pmtiles world.mbtiles

# MBTiles → disk (tile directory)
docker run -v $(pwd):/data techidiotsllc/pmtiles-mbtiles-util world.mbtiles tiles/

# Disk (tile directory) → MBTiles
docker run -v $(pwd):/data techidiotsllc/pmtiles-mbtiles-util tiles/ world.mbtiles

# PMTiles → disk
docker run -v $(pwd):/data techidiotsllc/pmtiles-mbtiles-util world.pmtiles tiles/

# Disk → PMTiles
docker run -v $(pwd):/data techidiotsllc/pmtiles-mbtiles-util tiles/ world.pmtiles
```

## With Options

```bash
# PMTiles → MBTiles with tile deduplication
docker run -v $(pwd):/data techidiotsllc/pmtiles-mbtiles-util --do_compression world.pmtiles world.mbtiles

# Dump metadata to terminal
docker run -v $(pwd):/data techidiotsllc/pmtiles-mbtiles-util world.pmtiles dumps
docker run -v $(pwd):/data techidiotsllc/pmtiles-mbtiles-util world.mbtiles dumps
```

## Large Files (Temp Directory)

For large conversions (multi-GB files), the PMTiles writer uses a temporary file during processing. By default this goes to `/tmp` inside the container. To ensure enough disk space and better I/O performance, you can mount a host directory at `/tmp`:

```bash
docker run \
  -v $(pwd):/data \
  -v /mnt/fast-disk/tmp:/tmp \
  techidiotsllc/pmtiles-mbtiles-util world.mbtiles world.pmtiles
```

## Input and Output in Different Directories

If your input and output are on different paths, mount them separately and use absolute paths:

```bash
docker run \
  -v /source/tiles:/source \
  -v /output/tiles:/output \
  techidiotsllc/pmtiles-mbtiles-util /source/world.mbtiles /output/world.pmtiles
```

## Specific Version

```bash
docker run -v $(pwd):/data techidiotsllc/pmtiles-mbtiles-util:v1.1.0 world.mbtiles world.pmtiles
```

## Building Locally

```bash
docker build -t pmtiles-mbtiles-util .
docker run -v $(pwd):/data pmtiles-mbtiles-util world.mbtiles world.pmtiles
```
