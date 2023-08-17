from setuptools import setup
setup(
        name = 'bulk_scrape_core',
        version = "0.1.0",
        packages = ['bulk_scrape_core'],
        install_requires=[
            'beautifulsoup4'
        ],
        entry_points = {
            'console_scripts': [
                'bulk-scrape = bulk_scrape_core.__main__:main'
                ]
            })
