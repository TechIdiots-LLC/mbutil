import os
import shutil
import json
import sqlite3
import unittest

from pmtiles_mbtiles_util import (
    mbtiles_to_pmtiles_cmd,
    pmtiles_to_mbtiles_cmd,
    disk_to_pmtiles,
    pmtiles_to_disk,
    normalize_metadata,
    prepare_metadata_for_mbtiles,
)


OUTPUT_DIR = 'test/output'
ONE_TILE_MBTILES = 'test/data/one_tile.mbtiles'
ONE_TILE_WEBP_MBTILES = 'test/data/one_tile_webp.mbtiles'


def _output(*parts):
    return os.path.join(OUTPUT_DIR, *parts)


class PMTilesConversionTestCase(unittest.TestCase):

    def setUp(self):
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

    # ------------------------------------------------------------------
    # MBTiles → PMTiles
    # ------------------------------------------------------------------

    def test_mbtiles_to_pmtiles_creates_file(self):
        out = _output('one_tile.pmtiles')
        mbtiles_to_pmtiles_cmd(ONE_TILE_MBTILES, out, silent=True)
        self.assertTrue(os.path.exists(out))
        self.assertGreater(os.path.getsize(out), 0)

    def test_mbtiles_to_pmtiles_valid_header(self):
        """Output file starts with PMTiles magic bytes."""
        out = _output('one_tile.pmtiles')
        mbtiles_to_pmtiles_cmd(ONE_TILE_MBTILES, out, silent=True)
        with open(out, 'rb') as f:
            magic = f.read(7)
        self.assertEqual(magic, b'PMTiles')

    # ------------------------------------------------------------------
    # PMTiles → MBTiles
    # ------------------------------------------------------------------

    def test_pmtiles_to_mbtiles_roundtrip(self):
        """Tile data survives MBTiles → PMTiles → MBTiles roundtrip."""
        pmtiles_path = _output('one_tile.pmtiles')
        mbtiles_out = _output('roundtrip.mbtiles')

        # Get source tile count
        src_con = sqlite3.connect(ONE_TILE_MBTILES)
        src_rows = list(src_con.execute("SELECT zoom_level, tile_column, tile_row FROM tiles"))
        src_con.close()

        mbtiles_to_pmtiles_cmd(ONE_TILE_MBTILES, pmtiles_path, silent=True)
        pmtiles_to_mbtiles_cmd(pmtiles_path, mbtiles_out, silent=True)

        self.assertTrue(os.path.exists(mbtiles_out))
        con = sqlite3.connect(mbtiles_out)
        rows = list(con.execute("SELECT zoom_level, tile_column, tile_row FROM tiles"))
        con.close()
        self.assertEqual(len(rows), len(src_rows))

    def test_pmtiles_to_mbtiles_metadata_preserved(self):
        """Metadata name survives MBTiles → PMTiles → MBTiles roundtrip."""
        # Read original name from source
        con = sqlite3.connect(ONE_TILE_MBTILES)
        original_name = dict(con.execute("SELECT name, value FROM metadata")).get('name', '')
        con.close()

        pmtiles_path = _output('one_tile.pmtiles')
        mbtiles_out = _output('roundtrip.mbtiles')
        mbtiles_to_pmtiles_cmd(ONE_TILE_MBTILES, pmtiles_path, silent=True)
        pmtiles_to_mbtiles_cmd(pmtiles_path, mbtiles_out, silent=True)

        con = sqlite3.connect(mbtiles_out)
        result_meta = dict(con.execute("SELECT name, value FROM metadata"))
        con.close()
        self.assertEqual(result_meta.get('name', ''), original_name)

    def test_pmtiles_to_mbtiles_scheme_tms(self):
        """Output MBTiles always has scheme=tms."""
        pmtiles_path = _output('one_tile.pmtiles')
        mbtiles_out = _output('roundtrip.mbtiles')
        mbtiles_to_pmtiles_cmd(ONE_TILE_MBTILES, pmtiles_path, silent=True)
        pmtiles_to_mbtiles_cmd(pmtiles_path, mbtiles_out, silent=True)

        con = sqlite3.connect(mbtiles_out)
        meta = dict(con.execute("SELECT name, value FROM metadata"))
        con.close()
        self.assertEqual(meta.get('scheme'), 'tms')

    # ------------------------------------------------------------------
    # Disk → PMTiles → Disk
    # ------------------------------------------------------------------

    def test_disk_to_pmtiles_creates_file(self):
        tiles_dir = _output('tiles')
        from pmtiles_mbtiles_util import mbtiles_to_disk
        mbtiles_to_disk(ONE_TILE_MBTILES, tiles_dir, silent=True)

        out = _output('from_disk.pmtiles')
        disk_to_pmtiles(tiles_dir, out, silent=True)
        self.assertTrue(os.path.exists(out))
        self.assertGreater(os.path.getsize(out), 0)

    def test_pmtiles_to_disk_creates_tile_files(self):
        pmtiles_path = _output('one_tile.pmtiles')
        mbtiles_to_pmtiles_cmd(ONE_TILE_MBTILES, pmtiles_path, silent=True)

        tiles_out = _output('tiles_from_pmtiles')
        pmtiles_to_disk(pmtiles_path, tiles_out, silent=True)

        self.assertTrue(os.path.exists(os.path.join(tiles_out, 'metadata.json')))
        # One tile at z/x/y = 0/0/0
        self.assertTrue(os.path.exists(os.path.join(tiles_out, '0', '0', '0.png')))

    def test_disk_pmtiles_disk_roundtrip(self):
        """Tile file survives disk → PMTiles → disk roundtrip."""
        tiles_dir = _output('tiles_original')
        from pmtiles_mbtiles_util import mbtiles_to_disk
        mbtiles_to_disk(ONE_TILE_MBTILES, tiles_dir, silent=True)

        pmtiles_path = _output('roundtrip.pmtiles')
        disk_to_pmtiles(tiles_dir, pmtiles_path, silent=True)

        tiles_out = _output('tiles_restored')
        pmtiles_to_disk(pmtiles_path, tiles_out, silent=True)

        original_tile = os.path.join(tiles_dir, '0', '0', '0.png')
        restored_tile = os.path.join(tiles_out, '0', '0', '0.png')
        self.assertTrue(os.path.exists(restored_tile))
        with open(original_tile, 'rb') as f:
            original_bytes = f.read()
        with open(restored_tile, 'rb') as f:
            restored_bytes = f.read()
        self.assertEqual(original_bytes, restored_bytes)

    # ------------------------------------------------------------------
    # PMTiles output must not contain 'scheme' in metadata
    # ------------------------------------------------------------------

    def test_pmtiles_output_has_no_scheme(self):
        """PMTiles output metadata must not contain a 'scheme' key."""
        from pmtiles.reader import Reader, MmapSource
        pmtiles_path = _output('one_tile.pmtiles')
        mbtiles_to_pmtiles_cmd(ONE_TILE_MBTILES, pmtiles_path, silent=True)
        with open(pmtiles_path, 'rb') as f:
            reader = Reader(MmapSource(f))
            meta = reader.metadata()
        self.assertNotIn('scheme', meta)


class MetadataHelperTestCase(unittest.TestCase):
    """Unit tests for normalize_metadata and prepare_metadata_for_mbtiles."""

    def test_normalize_metadata_parses_json_row(self):
        vector_layers = [{"id": "water", "fields": {}}]
        raw = {
            'name': 'Test',
            'format': 'pbf',
            'json': json.dumps({'vector_layers': vector_layers}),
        }
        result = normalize_metadata(raw)
        self.assertEqual(result['vector_layers'], vector_layers)
        self.assertNotIn('json', result)

    def test_normalize_metadata_passthrough(self):
        """Metadata without a 'json' row is returned unchanged."""
        raw = {'name': 'Test', 'format': 'png', 'minzoom': '0'}
        result = normalize_metadata(raw)
        self.assertEqual(result, raw)

    def test_prepare_metadata_roundtrip(self):
        """vector_layers survive normalize → prepare roundtrip."""
        vector_layers = [{"id": "roads", "fields": {"name": "String"}}]
        tilestats = {"layerCount": 1}
        raw = {
            'name': 'Test',
            'format': 'pbf',
            'json': json.dumps({'vector_layers': vector_layers, 'tilestats': tilestats}),
        }
        normalized = normalize_metadata(raw)
        packed = dict(prepare_metadata_for_mbtiles(normalized))

        # Should have a 'json' key with both fields encoded
        self.assertIn('json', packed)
        decoded = json.loads(packed['json'])
        self.assertEqual(decoded['vector_layers'], vector_layers)
        self.assertEqual(decoded['tilestats'], tilestats)

    def test_prepare_metadata_no_json_row_when_no_vector_layers(self):
        """Raster metadata should not produce a 'json' row."""
        raw = {'name': 'Test', 'format': 'png'}
        packed = dict(prepare_metadata_for_mbtiles(raw))
        self.assertNotIn('json', packed)


class WebpFormatPreservationTestCase(unittest.TestCase):
    """Regression tests for webp format being preserved through conversions.

    Previously, the --image_format CLI option defaulted to 'png', which meant
    mbtiles_to_pmtiles_cmd always received format='png' in kwargs — overriding
    the 'webp' value stored in the MBTiles metadata.
    """

    def setUp(self):
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.webp_mbtiles = ONE_TILE_WEBP_MBTILES

    def tearDown(self):
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

    def _read_pmtiles_header_and_meta(self, path):
        import sys
        import os as _os
        _pmtiles_path = _os.path.abspath(_os.path.join(
            _os.path.dirname(__file__), '..', 'PMTiles', 'python', 'pmtiles'))
        if _pmtiles_path not in sys.path:
            sys.path.append(_pmtiles_path)
        from pmtiles.reader import Reader, MmapSource
        with open(path, 'rb') as f:
            reader = Reader(MmapSource(f))
            return reader.header(), reader.metadata()

    def test_webp_format_preserved_in_pmtiles_header(self):
        """mbtiles→pmtiles: tile_type in PMTiles header must reflect webp, not png."""
        import sys
        import os as _os
        _pmtiles_path = _os.path.abspath(_os.path.join(
            _os.path.dirname(__file__), '..', 'PMTiles', 'python', 'pmtiles'))
        if _pmtiles_path not in sys.path:
            sys.path.append(_pmtiles_path)
        from pmtiles.tile import TileType

        out = _output('webp.pmtiles')
        # No format kwarg passed — should auto-detect 'webp' from metadata
        mbtiles_to_pmtiles_cmd(self.webp_mbtiles, out, silent=True)

        header, _ = self._read_pmtiles_header_and_meta(out)
        self.assertEqual(header['tile_type'], TileType.WEBP,
                         "PMTiles header tile_type should be WEBP, got %s" % header['tile_type'])

    def test_webp_format_preserved_in_pmtiles_metadata(self):
        """mbtiles→pmtiles: 'format' key in PMTiles metadata must be 'webp'."""
        out = _output('webp.pmtiles')
        mbtiles_to_pmtiles_cmd(self.webp_mbtiles, out, silent=True)

        _, meta = self._read_pmtiles_header_and_meta(out)
        self.assertEqual(meta.get('format'), 'webp',
                         "PMTiles metadata format should be 'webp', got %r" % meta.get('format'))

    def test_explicit_format_flag_overrides_metadata(self):
        """Explicit --image_format=png overrides source metadata format."""
        import sys
        import os as _os
        _pmtiles_path = _os.path.abspath(_os.path.join(
            _os.path.dirname(__file__), '..', 'PMTiles', 'python', 'pmtiles'))
        if _pmtiles_path not in sys.path:
            sys.path.append(_pmtiles_path)
        from pmtiles.tile import TileType

        out = _output('webp_forced_png.pmtiles')
        mbtiles_to_pmtiles_cmd(self.webp_mbtiles, out, silent=True, format='png')

        header, meta = self._read_pmtiles_header_and_meta(out)
        self.assertEqual(header['tile_type'], TileType.PNG)
        self.assertEqual(meta.get('format'), 'png')

    def test_webp_format_survives_pmtiles_to_mbtiles_roundtrip(self):
        """webp format survives mbtiles → pmtiles → mbtiles roundtrip."""
        pmtiles_path = _output('webp.pmtiles')
        mbtiles_out = _output('webp_roundtrip.mbtiles')

        mbtiles_to_pmtiles_cmd(self.webp_mbtiles, pmtiles_path, silent=True)
        pmtiles_to_mbtiles_cmd(pmtiles_path, mbtiles_out, silent=True)

        con = sqlite3.connect(mbtiles_out)
        meta = dict(con.execute("SELECT name, value FROM metadata"))
        con.close()
        self.assertEqual(meta.get('format'), 'webp',
                         "format should be 'webp' after roundtrip, got %r" % meta.get('format'))


if __name__ == '__main__':
    unittest.main()
