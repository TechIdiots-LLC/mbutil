# MBUtil

MBUtil is a utility for importing and exporting the [MBTiles](http://mbtiles.org/) format.

## Installation

Git checkout (requires git)

    git clone https://github.com/acalcutt/mbutil.git
    cd mbutil
    # get usage
    ./mb-util -h

Then to install the mb-util command globally:

    sudo python setup.py install
    # then you can run:
    mb-util

## Usage

    $ mb-util -h
    Usage: mb-util [options] input output

    Examples:
        Export an mbtiles file to a directory of files:
        $ mb-util world.mbtiles tiles # tiles must not already exist

        Import a directory of tiles into an mbtiles file:
        $ mb-util tiles world.mbtiles # mbtiles file must not already exist

    Options:
      -h, --help            Show this help message and exit
      --scheme=SCHEME       Tiling scheme of the tiles. Default is "xyz" (z/x/y),
                            other options are "tms" which is also z/x/y
                            but uses a flipped y coordinate, and "wms" which replicates
                            the MapServer WMS TileCache directory structure
                            "z/000/000/x/000/000/y.png", "zyx" which is the format
                            vips dzsave --layout google uses, "ags" for ArcGIS Server,
                            and "gwc" for GeoWebCache.
      --image_format=FORMAT
                            The format of the image tiles, either png, jpg, webp or pbf
      --grid_callback=CALLBACK
                            Option to control JSONP callback for UTFGrid tiles. If
                            grids are not used as JSONP, you can
                            remove callbacks specifying --grid_callback=""
      --do_compression      Enable tile deduplication to reduce mbtiles file size.
                            Uses hash-based deduplication to store each unique tile
                            only once, with references for duplicate tiles.
      --hash_type=HASH_TYPE
                            Hash algorithm for tile deduplication (use with --do_compression).
                            Options: fnv1a (fast, default), sha256 (most secure),
                            sha256_truncated (balanced), md5 (legacy)
      --silent              Dictate whether the operations should run silently

## Examples

Export an `mbtiles` file to files on the filesystem:

    mb-util World_Light.mbtiles adirectory

Import a directory into a `mbtiles` file:

    mb-util directory World_Light.mbtiles

Import with tile deduplication (reduces file size):

    mb-util --do_compression tiles World_Light.mbtiles

Import with deduplication using SHA256 for maximum collision resistance:

    mb-util --do_compression --hash_type sha256 tiles World_Light.mbtiles

Export using the TMS scheme:

    mb-util --scheme=tms World_Light.mbtiles tiles

## Tile Deduplication

When importing tiles with `--do_compression`, MBUtil uses hash-based deduplication to significantly reduce file size. This is especially useful for:

- **Map tiles with repetitive content** (ocean tiles, empty areas, borders)
- **Vector tiles** where many tiles may be identical
- **Large datasets** spanning multiple zoom levels

### How it works

Instead of storing duplicate tiles multiple times, MBUtil:
1. Computes a hash of each tile's content
2. Stores each unique tile only once in a `tiles_data` table
3. Creates references to unique tiles in a `tiles_shallow` table
4. Presents a standard `tiles` view for compatibility

### Hash Types

| Hash Type | Bits | Speed | Best For |
|-----------|------|-------|----------|
| **fnv1a** (default) | 64 | Fastest | General use, good distribution |
| **sha256_truncated** | 64 | Medium | Balance of speed and standardization |
| **sha256** | 256 | Medium | Maximum collision resistance, critical data |
| **md5** | 128 | Fast | Legacy compatibility |

**Collision risk at 10 million tiles:**
- 64-bit hashes (fnv1a, sha256_truncated): ~0.001% risk
- 256-bit hash (sha256): effectively zero risk
- 128-bit hash (md5): ~0.00001% risk

### Example deduplication results

For a typical map with ocean tiles:
```
Total tiles: 1,000,000
Unique tiles: 250,000
Duplicate tiles: 750,000 (75%)
Space saved: ~3.5 GB (assuming ~5KB average tile size)
```

## Requirements

* Python `>= 2.6`

## Metadata

MBUtil imports and exports metadata as JSON, in the root of the tile directory, as a file named `metadata.json`.

```javascript
{
    "name": "World Light",
    "description": "A Test Metadata",
    "version": "3"
}
```

## Testing

This project uses [nosetests](http://readthedocs.org/docs/nose/en/latest/) for testing. Install nosetests:

    pip install nose

or

    easy_install nose
    
Then run:

    nosetests

## Performance Tips

- Use `--do_compression` for datasets with repetitive tiles
- Use `--silent` flag for faster processing without logging overhead
- For very large datasets (100GB+), ensure sufficient disk space for SQLite temp files

## See Also

* [node-mbtiles provides mbpipe](https://github.com/mapbox/node-mbtiles/wiki/Post-processing-MBTiles-with-MBPipe), a useful utility.
* [mbliberator](https://github.com/calvinmetcalf/mbliberator) a similar program but in node.
* [MBTiles Specification](https://github.com/mapbox/mbtiles-spec)

## License

BSD - see LICENSE.md

## Authors

- Tom MacWright (tmcw)
- Dane Springmeyer (springmeyer)
- Mathieu Leplatre (leplatrem)
- Andrew Calcutt (acalcutt)
