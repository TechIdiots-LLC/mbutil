import os
import shutil
import json
import unittest

from mbutil import mbtiles_to_disk, disk_to_mbtiles


OUTPUT_DIR = 'test/output'


class MBTilesTestCase(unittest.TestCase):

    def setUp(self):
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

    def tearDown(self):
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

    def test_mbtiles_to_disk(self):
        mbtiles_to_disk('test/data/one_tile.mbtiles', OUTPUT_DIR)
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, '0/0/0.png')))
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, 'metadata.json')))

    def test_mbtiles_to_disk_and_back(self):
        mbtiles_to_disk('test/data/one_tile.mbtiles', OUTPUT_DIR)
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, '0/0/0.png')))
        disk_to_mbtiles(OUTPUT_DIR + '/', os.path.join(OUTPUT_DIR, 'one.mbtiles'))
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, 'one.mbtiles')))

    def test_utf8grid_mbtiles_to_disk(self):
        mbtiles_to_disk('test/data/utf8grid.mbtiles', OUTPUT_DIR)
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, '0/0/0.grid.json')))
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, '0/0/0.png')))
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, 'metadata.json')))

    def test_utf8grid_disk_to_mbtiles(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        mbtiles_to_disk('test/data/utf8grid.mbtiles', os.path.join(OUTPUT_DIR, 'original'), callback=None)
        disk_to_mbtiles(os.path.join(OUTPUT_DIR, 'original') + '/', os.path.join(OUTPUT_DIR, 'imported.mbtiles'))
        mbtiles_to_disk(os.path.join(OUTPUT_DIR, 'imported.mbtiles'), os.path.join(OUTPUT_DIR, 'imported'), callback=None)
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, 'imported/0/0/0.grid.json')))
        with open(os.path.join(OUTPUT_DIR, 'original/0/0/0.grid.json')) as f:
            original = json.load(f)
        with open(os.path.join(OUTPUT_DIR, 'imported/0/0/0.grid.json')) as f:
            imported = json.load(f)
        self.assertEqual(original['data']['77'], imported['data']['77'])
        self.assertEqual(original['data']['77'], {'ISO_A2': 'FR'})

    def test_mbtiles_to_disk_utfgrid_callback(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        for c in ['null', 'foo']:
            mbtiles_to_disk('test/data/utf8grid.mbtiles', os.path.join(OUTPUT_DIR, c), callback=c)
            with open(os.path.join(OUTPUT_DIR, c, '0/0/0.grid.json')) as f:
                content = f.read()
            prefix = content.split('{')[0]
            if c == 'foo':
                self.assertEqual(prefix, 'foo(')
            else:
                self.assertEqual(prefix, '')

    def test_disk_to_mbtiles_zyx(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        disk_to_mbtiles('test/data/tiles/zyx', os.path.join(OUTPUT_DIR, 'zyx.mbtiles'), scheme='zyx', format='png')
        mbtiles_to_disk(os.path.join(OUTPUT_DIR, 'zyx.mbtiles'), os.path.join(OUTPUT_DIR, 'tiles'), callback=None)
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, 'tiles/3/1/5.png')))


if __name__ == '__main__':
    unittest.main()
