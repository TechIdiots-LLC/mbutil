from setuptools import setup

setup(
    name='mbutil',
    version='0.4.0',
    author='Andrew Calcutt',
    author_email='info@techidiots.net',
    packages=['mbutil'],
    scripts=['mb-util'],
    url='https://github.com/TechIdiots-LLC/mbutil',
    license='LICENSE.md',
    description='An importer and exporter for MBTiles and PMTiles',
    long_description=open('README.md').read() if __import__('os').path.exists('README.md') else '',
)
