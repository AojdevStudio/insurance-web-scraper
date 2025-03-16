from setuptools import setup, find_packages

setup(
    name="dental_insurance_guidelines_web_scraper",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "scrapy>=2.11.0",
        "beautifulsoup4>=4.12.3",
        "lxml>=5.1.0",
        "selenium>=4.18.1",
        "fake-useragent>=1.4.0",
        "pdfplumber>=0.10.3",
        "PyPDF2>=3.0.1",
        "pandas>=2.2.0",
        "numpy>=1.26.3",
        "pymongo>=4.6.1",
        "loguru>=0.7.2",
    ],
    extras_require={
        "test": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.5",
            "pytest-mock>=3.12.0",
        ],
        "docs": [
            "Sphinx>=7.2.6",
            "sphinx-rtd-theme>=2.0.0",
        ],
    },
) 