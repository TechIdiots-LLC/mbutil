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
# The import name is unaffected. This installs as pmtiles-mbtiles-util and is
# still `import mbutil`, still providing the `mb-util` command.
setup(
    name='pmtiles-mbtiles-util',
    version='0.4.6',
    author='Andrew Calcutt',
    author_email='info@techidiots.net',
    maintainer='TechIdiots-LLC',
    packages=['mbutil'],
    # console_scripts, not scripts=['mb-util']: a bare script is copied verbatim,
    # which works on Linux but leaves Windows with no launcher and no runnable
    # `mb-util` command. The repo keeps ./mb-util as a shim for source checkouts
    # and the Docker entrypoint.
    entry_points={
        'console_scripts': [
            'mb-util = mbutil.cli:main',
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
