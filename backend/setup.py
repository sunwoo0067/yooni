from setuptools import setup, find_packages

setup(
    name="yoonni-backend",
    version="0.1.0",
    description="E-commerce integration backend for Korean marketplaces",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "psycopg2-binary>=2.9.9",
        "python-dotenv>=1.0.0",
        "pandas>=2.1.4",
        "openpyxl>=3.1.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "black>=23.12.1",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "logging": [
            "colorlog>=6.8.0",
            "python-json-logger>=2.0.7",
        ],
    },
)