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
# The import name is unaffected. This installs as mb-util and is still
# `import mbutil`, still providing the `mb-util` command.
setup(
    name='mb-util',
    version='0.4.6',
    author='Andrew Calcutt',
    author_email='info@techidiots.net',
    maintainer='TechIdiots-LLC',
    packages=['mbutil'],
    scripts=['mb-util'],
    url='https://github.com/TechIdiots-LLC/mb-util',
    project_urls={
        'Changelog': 'https://github.com/TechIdiots-LLC/mb-util/blob/master/CHANGELOG.md',
        'Source': 'https://github.com/TechIdiots-LLC/mb-util',
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
    # In a source checkout the PMTiles library is the git submodule, found via
    # a relative path. An installed package has no submodule beside it, so
    # without this dependency every PMTiles command would fall back to the
    # ImportError stubs and silently do nothing. 3.7.0 is the first release
    # carrying TileType.MLT.
    install_requires=['pmtiles>=3.7.0'],
)
