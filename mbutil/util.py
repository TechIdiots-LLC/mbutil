#!/usr/bin/env python

# MBUtil: a tool for MBTiles files
# Supports importing, exporting, and more
#
# (c) Development Seed 2012
# Licensed under BSD

# for additional reference on schema see:
# https://github.com/mapbox/node-mbtiles/blob/master/lib/schema.sql

import sqlite3, sys, logging, time, os, json, zlib, re, hashlib

logger = logging.getLogger(__name__)

def flip_y(zoom, y):
    return (2**zoom-1) - y

def fnv1a(data):
    """
    FNV-1a hash function for tile deduplication.
    Fast, non-cryptographic hash with good distribution.
    """
    h = 14695981039346656037
    for b in data:
        h ^= b
        h *= 1099511628211
        h &= 0xFFFFFFFFFFFFFFFF  # 64-bit mask
    return str(h)

def mbtiles_setup(cur, use_deduplication=False):
    """
    Set up MBTiles database schema.
    
    Args:
        cur: Database cursor
        use_deduplication: If True, uses tiles_shallow + tiles_data schema for deduplication.
                          If False, uses simple tiles table (original mbutil behavior).
    """
    if use_deduplication:
        # Deduplication schema: separate tile data from tile locations
        cur.execute("""
            CREATE TABLE tiles_shallow (
                TILES_COL_Z integer,
                TILES_COL_X integer,
                TILES_COL_Y integer,
                TILES_COL_DATA_ID text,
                primary key(TILES_COL_Z,TILES_COL_X,TILES_COL_Y)
            ) without rowid;
        """)
        cur.execute("""
            CREATE TABLE tiles_data (
                tile_data_id text primary key,
                tile_data blob
            );
        """)
        cur.execute("""
            CREATE VIEW tiles AS
            SELECT
                tiles_shallow.TILES_COL_Z as zoom_level,
                tiles_shallow.TILES_COL_X as tile_column,
                tiles_shallow.TILES_COL_Y as tile_row,
                tiles_data.tile_data as tile_data
            FROM tiles_shallow
            JOIN tiles_data ON tiles_shallow.TILES_COL_DATA_ID = tiles_data.tile_data_id;
        """)
        cur.execute("""
            CREATE UNIQUE INDEX tiles_shallow_index on tiles_shallow (TILES_COL_Z, TILES_COL_X, TILES_COL_Y);
        """)
    else:
        # Simple schema: original mbutil behavior
        cur.execute("""
            CREATE TABLE tiles (
                zoom_level integer,
                tile_column integer,
                tile_row integer,
                tile_data blob);
        """)
        cur.execute("""
            CREATE UNIQUE INDEX tile_index on tiles
                (zoom_level, tile_column, tile_row);
        """)

    # Common tables for both schemas
    cur.execute("""CREATE TABLE metadata
        (name text, value text);""")
    cur.execute("""CREATE TABLE grids (zoom_level integer, tile_column integer,
    tile_row integer, grid blob);""")
    cur.execute("""CREATE TABLE grid_data (zoom_level integer, tile_column
    integer, tile_row integer, key_name text, key_json text);""")
    cur.execute("""CREATE UNIQUE INDEX name on metadata (name);""")

def mbtiles_connect(mbtiles_file, silent):
    try:
        con = sqlite3.connect(mbtiles_file)
        return con
    except Exception as e:
        if not silent:
            logger.error("Could not connect to database")
            logger.exception(e)
        sys.exit(1)

def optimize_connection(cur):
    cur.execute("""PRAGMA synchronous=0""")
    cur.execute("""PRAGMA locking_mode=EXCLUSIVE""")
    cur.execute("""PRAGMA journal_mode=DELETE""")

def optimize_database(cur, silent):
    if not silent:
        logger.debug('analyzing db')
    cur.execute("""ANALYZE;""")
    if not silent:
        logger.debug('cleaning db')

    # Workaround for python>=3.6.0,python<3.6.2
    # https://bugs.python.org/issue28518
    cur.isolation_level = None
    cur.execute("""VACUUM;""")
    cur.isolation_level = '' # reset default value of isolation_level

def get_dirs(path):
    return [name for name in os.listdir(path)
        if os.path.isdir(os.path.join(path, name))]

def disk_to_mbtiles(directory_path, mbtiles_file, **kwargs):
    """
    Import tiles from directory to MBTiles file.
    
    If compression=True, uses hash-based deduplication during import.
    If compression=False, uses simple schema without deduplication (original mbutil behavior).
    """
    silent = kwargs.get('silent')
    use_compression = kwargs.get('compression', False)

    if not silent:
        logger.info("Importing disk to MBTiles")
        if use_compression:
            logger.info("Using hash-based deduplication")
        logger.debug("%s --> %s" % (directory_path, mbtiles_file))

    con = mbtiles_connect(mbtiles_file, silent)
    cur = con.cursor()
    optimize_connection(cur)
    mbtiles_setup(cur, use_deduplication=use_compression)
    
    image_format = kwargs.get('format', 'png')

    # Load metadata
    try:
        metadata = json.load(open(os.path.join(directory_path, 'metadata.json'), 'r'))
        image_format = kwargs.get('format')
        for name, value in metadata.items():
            cur.execute("""INSERT INTO metadata (name, value) VALUES (?, ?)""",
                (name, value))
        if not silent:
            logger.info('metadata from metadata.json restored')
    except IOError:
        if not silent:
            logger.warning('metadata.json not found')

    # Statistics tracking
    stats = {
        'total_tiles': 0,
        'unique_tiles': 0,
        'duplicate_tiles': 0,
        'total_size': 0,
        'unique_size': 0
    }
    
    count = 0
    start_time = time.time()
    
    # Batch processing
    BATCH_SIZE = 1000
    tile_data_batch = []
    tile_shallow_batch = []
    simple_tile_batch = []

    def flush_batches():
        """Flush accumulated batches to database."""
        nonlocal tile_data_batch, tile_shallow_batch, simple_tile_batch
        
        if use_compression:
            if tile_data_batch:
                # Get count before insert to track statistics
                pre_count = cur.execute("SELECT COUNT(*) FROM tiles_data").fetchone()[0]
                
                cur.executemany(
                    """INSERT OR IGNORE INTO tiles_data 
                    (tile_data_id, tile_data) VALUES (?, ?);""",
                    tile_data_batch
                )
                
                # Calculate how many were actually inserted (not ignored)
                post_count = cur.execute("SELECT COUNT(*) FROM tiles_data").fetchone()[0]
                actually_inserted = post_count - pre_count
                stats['unique_tiles'] += actually_inserted
                stats['duplicate_tiles'] += len(tile_data_batch) - actually_inserted
                
                tile_data_batch = []
            
            if tile_shallow_batch:
                cur.executemany(
                    """INSERT INTO tiles_shallow 
                    (TILES_COL_Z, TILES_COL_X, TILES_COL_Y, TILES_COL_DATA_ID) 
                    VALUES (?, ?, ?, ?);""",
                    tile_shallow_batch
                )
                tile_shallow_batch = []
        else:
            if simple_tile_batch:
                cur.executemany(
                    """INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data) 
                    VALUES (?, ?, ?, ?);""",
                    simple_tile_batch
                )
                simple_tile_batch = []
        
        con.commit()

    # Process tiles
    for zoom_dir in get_dirs(directory_path):
        if kwargs.get("scheme") == 'ags':
            if not "L" in zoom_dir:
                if not silent:
                    logger.warning("You appear to be using an ags scheme on an non-arcgis Server cache.")
            z = int(zoom_dir.replace("L", ""))
        elif kwargs.get("scheme") == 'gwc':
            z = int(zoom_dir[-2:])
        else:
            if "L" in zoom_dir:
                if not silent:
                    logger.warning("You appear to be using a %s scheme on an arcgis Server cache. Try using --scheme=ags instead" % kwargs.get("scheme"))
            z = int(zoom_dir)
            
        for row_dir in get_dirs(os.path.join(directory_path, zoom_dir)):
            if kwargs.get("scheme") == 'ags':
                y = flip_y(z, int(row_dir.replace("R", ""), 16))
            elif kwargs.get("scheme") == 'gwc':
                pass
            elif kwargs.get("scheme") == 'zyx':
                y = flip_y(int(z), int(row_dir))
            else:
                x = int(row_dir)
                
            for current_file in os.listdir(os.path.join(directory_path, zoom_dir, row_dir)):
                if current_file == ".DS_Store":
                    if not silent:
                        logger.warning("Your OS is MacOS, and the .DS_Store file will be ignored.")
                    continue
                    
                file_name, ext = current_file.split('.', 1)
                f = open(os.path.join(directory_path, zoom_dir, row_dir, current_file), 'rb')
                file_content = f.read()
                f.close()
                
                if kwargs.get('scheme') == 'xyz':
                    y = flip_y(int(z), int(file_name))
                elif kwargs.get("scheme") == 'ags':
                    x = int(file_name.replace("C", ""), 16)
                elif kwargs.get("scheme") == 'gwc':
                    x, y = file_name.split('_')
                    x = int(x)
                    y = int(y)
                elif kwargs.get("scheme") == 'zyx':
                    x = int(file_name)
                else:
                    y = int(file_name)

                if ext == image_format:
                    if not silent and count < 10:  # Only log first 10 for debugging
                        logger.debug(' Read tile from Zoom (z): %i\tCol (x): %i\tRow (y): %i' % (z, x, y))
                    
                    stats['total_tiles'] += 1
                    stats['total_size'] += len(file_content)
                    
                    if use_compression:
                        # Hash-based deduplication
                        tile_hash = fnv1a(file_content)
                        
                        # Always add to batch - INSERT OR IGNORE will handle duplicates
                        tile_data_batch.append((tile_hash, sqlite3.Binary(file_content)))
                        
                        # Track size for potential savings (actual dedup stats calculated on flush)
                        
                        # Always insert the tile reference
                        tile_shallow_batch.append((z, x, y, tile_hash))
                    else:
                        # Simple insertion without deduplication
                        simple_tile_batch.append((z, x, y, sqlite3.Binary(file_content)))
                        stats['unique_tiles'] += 1
                        stats['unique_size'] += len(file_content)
                    
                    count += 1
                    
                    # Flush batches periodically
                    if count % BATCH_SIZE == 0:
                        flush_batches()
                        if not silent:
                            elapsed = time.time() - start_time
                            rate = count / elapsed if elapsed > 0 else 0
                            logger.info(" %s tiles processed (%d tiles/sec)" % (count, rate))
                            if use_compression and stats['total_tiles'] > 0:
                                # Calculate unique size based on current tiles_data count
                                unique_count = cur.execute("SELECT COUNT(*) FROM tiles_data").fetchone()[0]
                                dedup_ratio = ((stats['total_tiles'] - unique_count) / stats['total_tiles']) * 100
                                logger.info(" Deduplication: %d unique, %d total (%.1f%% duplicates)" % 
                                          (unique_count, stats['total_tiles'], dedup_ratio))
                    
                elif ext == 'grid.json':
                    if not silent:
                        logger.debug(' Read grid from Zoom (z): %i\tCol (x): %i\tRow (y): %i' % (z, x, y))
                    
                    # Remove potential callback with regex
                    file_content = file_content.decode('utf-8')
                    has_callback = re.match(r'[\w\s=+-/]+\(({(.|\n)*})\);?', file_content)
                    if has_callback:
                        file_content = has_callback.group(1)
                    utfgrid = json.loads(file_content)

                    data = utfgrid.pop('data')
                    compressed = zlib.compress(json.dumps(utfgrid).encode())
                    cur.execute("""INSERT INTO grids (zoom_level, tile_column, tile_row, grid) 
                                VALUES (?, ?, ?, ?) """, 
                              (z, x, y, sqlite3.Binary(compressed)))
                    
                    grid_keys = [k for k in utfgrid['keys'] if k != ""]
                    for key_name in grid_keys:
                        key_json = data[key_name]
                        cur.execute("""INSERT INTO grid_data (zoom_level, tile_column, tile_row, key_name, key_json) 
                                    VALUES (?, ?, ?, ?, ?);""", 
                                  (z, x, y, key_name, json.dumps(key_json)))

    # Flush any remaining batches
    flush_batches()

    if not silent:
        logger.debug('Tiles (and grids) inserted.')
        logger.info("Import complete:")
        logger.info(" Total tiles: %d" % stats['total_tiles'])
        if use_compression:
            # Get final counts from database
            unique_count = cur.execute("SELECT COUNT(*) FROM tiles_data").fetchone()[0]
            duplicate_count = stats['total_tiles'] - unique_count
            
            logger.info(" Unique tiles: %d" % unique_count)
            logger.info(" Duplicate tiles: %d" % duplicate_count)
            if stats['total_tiles'] > 0:
                dedup_ratio = (duplicate_count / stats['total_tiles']) * 100
                logger.info(" Deduplication ratio: %.1f%%" % dedup_ratio)
            logger.info(" Total size: %s" % format_bytes(stats['total_size']))
            
            # Estimate unique size (we can't know exactly without tracking each unique tile's size)
            # This is approximate based on deduplication ratio
            if duplicate_count > 0:
                avg_tile_size = stats['total_size'] / stats['total_tiles']
                unique_size = unique_count * avg_tile_size
                space_saved = stats['total_size'] - unique_size
                savings_pct = (space_saved / stats['total_size']) * 100
                logger.info(" Estimated space saved: %s (%.1f%%)" % (format_bytes(space_saved), savings_pct))

    optimize_database(con, silent)

def format_bytes(size):
    """Format bytes as human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return "%3.1f %s" % (size, unit)
        size /= 1024.0
    return "%.1f TB" % size

def mbtiles_metadata_to_disk(mbtiles_file, **kwargs):
    silent = kwargs.get('silent')
    if not silent:
        logger.debug("Exporting MBTiles metadata from %s" % (mbtiles_file))
    con = mbtiles_connect(mbtiles_file, silent)
    metadata = dict(con.execute('SELECT name, value FROM metadata;').fetchall())
    if not silent:
        logger.debug(json.dumps(metadata, indent=2))

def mbtiles_to_disk(mbtiles_file, directory_path, **kwargs):
    silent = kwargs.get('silent')
    if not silent:
        logger.debug("Exporting MBTiles to disk")
        logger.debug("%s --> %s" % (mbtiles_file, directory_path))
    
    con = mbtiles_connect(mbtiles_file, silent)
    os.mkdir("%s" % directory_path)
    
    metadata = dict(con.execute('SELECT name, value FROM metadata;').fetchall())
    json.dump(metadata, open(os.path.join(directory_path, 'metadata.json'), 'w'), indent=4)
    
    count = con.execute('SELECT count(zoom_level) FROM tiles;').fetchone()[0]
    done = 0
    base_path = directory_path
    
    if not os.path.isdir(base_path):
        os.makedirs(base_path)

    # If interactivity
    formatter = metadata.get('formatter')
    if formatter:
        layer_json = os.path.join(base_path, 'layer.json')
        formatter_json = {"formatter": formatter}
        open(layer_json, 'w').write(json.dumps(formatter_json))

    tiles = con.execute('SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles;')
    t = tiles.fetchone()
    
    while t:
        z = t[0]
        x = t[1]
        y = t[2]
        
        if kwargs.get('scheme') == 'xyz':
            y = flip_y(z, y)
            if not silent:
                logger.debug('flipping')
            tile_dir = os.path.join(base_path, str(z), str(x))
        elif kwargs.get('scheme') == 'wms':
            tile_dir = os.path.join(base_path,
                "%02d" % (z),
                "%03d" % (int(x) / 1000000),
                "%03d" % ((int(x) / 1000) % 1000),
                "%03d" % (int(x) % 1000),
                "%03d" % (int(y) / 1000000),
                "%03d" % ((int(y) / 1000) % 1000))
        else:
            tile_dir = os.path.join(base_path, str(z), str(x))
        
        if not os.path.isdir(tile_dir):
            os.makedirs(tile_dir)
        
        if kwargs.get('scheme') == 'wms':
            tile = os.path.join(tile_dir, '%03d.%s' % (int(y) % 1000, kwargs.get('format', 'png')))
        else:
            tile = os.path.join(tile_dir, '%s.%s' % (y, kwargs.get('format', 'png')))
        
        f = open(tile, 'wb')
        f.write(t[3])
        f.close()
        
        done = done + 1
        if not silent and (done % 100 == 0 or done == count):
            logger.info('%s / %s tiles exported' % (done, count))
        
        t = tiles.fetchone()

    # Grids
    callback = kwargs.get('callback')
    done = 0
    
    try:
        count = con.execute('SELECT count(zoom_level) FROM grids;').fetchone()[0]
        grids = con.execute('SELECT zoom_level, tile_column, tile_row, grid FROM grids;')
        g = grids.fetchone()
    except sqlite3.OperationalError:
        g = None  # no grids table
    
    while g:
        zoom_level = g[0]  # z
        tile_column = g[1]  # x
        y = g[2]  # y
        
        grid_data_cursor = con.execute('''SELECT key_name, key_json FROM
            grid_data WHERE
            zoom_level = %(zoom_level)d AND
            tile_column = %(tile_column)d AND
            tile_row = %(y)d;''' % locals())
        
        if kwargs.get('scheme') == 'xyz':
            y = flip_y(zoom_level, y)
        
        grid_dir = os.path.join(base_path, str(zoom_level), str(tile_column))
        if not os.path.isdir(grid_dir):
            os.makedirs(grid_dir)
        
        grid = os.path.join(grid_dir, '%s.grid.json' % (y))
        f = open(grid, 'w')
        grid_json = json.loads(zlib.decompress(g[3]).decode('utf-8'))
        
        # Join up with the grid 'data' which is in pieces when stored in mbtiles file
        grid_data = grid_data_cursor.fetchone()
        data = {}
        while grid_data:
            data[grid_data[0]] = json.loads(grid_data[1])
            grid_data = grid_data_cursor.fetchone()
        
        grid_json['data'] = data
        
        if callback in (None, "", "false", "null"):
            f.write(json.dumps(grid_json))
        else:
            f.write('%s(%s);' % (callback, json.dumps(grid_json)))
        
        f.close()
        done = done + 1
        
        if not silent:
            logger.info('%s / %s grids exported' % (done, count))
        
        g = grids.fetchone()
