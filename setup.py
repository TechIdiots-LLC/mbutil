import os

from setuptools import setup

long_description = ''
if os.path.exists('README.md'):
    with open('README.md', encoding='utf-8') as f:
        long_description = f.read()

# The distribution name is not "mbutil": that belongs to mapbox on PyPI, last
# published in 2018. PyPI project names are one flat global namespace -- an
# organisation account owns projects but does not scope their names, so there
# is no techidiots-llc/mbutil to publish under.
#
# Nor is it "mb-util": PyPI rejects names that match an existing project once
# separators are stripped, and "mb-util" reduces to "mbutil".
#
# The import package and the command match the distribution rather than keeping
# upstream's. mapbox's mbutil ships `packages=['mbutil']` and `scripts=['mb-util']`,
# so reusing either name means both distributions write the same files: pip
# installs them over each other without warning, and uninstalling one breaks the
# other.
setup(
    name='pmtiles-mbtiles-util',
    version='1.1.0',
    author='Andrew Calcutt',
    author_email='info@techidiots.net',
    maintainer='TechIdiots-LLC',
    packages=['pmtiles_mbtiles_util'],
    # console_scripts, not scripts=[...]: a bare script is copied verbatim, which
    # works on Linux but leaves Windows with no launcher and no runnable command.
    # The repo keeps ./pmtiles-mbtiles-util as a shim for source checkouts.
    entry_points={
        'console_scripts': [
            'pmtiles-mbtiles-util = pmtiles_mbtiles_util.cli:main',
        ],
    },
    url='https://github.com/TechIdiots-LLC/pmtiles-mbtiles-util',
    project_urls={
        'Changelog': 'https://github.com/TechIdiots-LLC/pmtiles-mbtiles-util/blob/master/CHANGELOG.md',
        'Source': 'https://github.com/TechIdiots-LLC/pmtiles-mbtiles-util',
        'Upstream': 'https://github.com/mapbox/mbutil',
    },
    license='BSD-3-Clause',
    description='An importer and exporter for MBTiles and PMTiles',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='mbtiles pmtiles mvt mlt tiles gis',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Scientific/Engineering :: GIS',
    ],
    python_requires='>=3.9',
    # Without this every PMTiles command falls back to the ImportError stubs
    # and silently does nothing. 3.7.0 is the first release carrying
    # TileType.MLT.
    install_requires=['pmtiles>=3.7.0'],
)
