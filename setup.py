from setuptools import setup, find_packages

setup(
    name="data-quality-framework",
    version="0.1.0",
    description="A reusable data quality framework for lakehouse-style ETL pipelines",
    author="Data Engineering Team",
    author_email="dev@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "pandas>=2.0.0",
        "pandera>=0.18.0",
        "pyyaml>=6.0.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
