#!/usr/bin/env python3
"""
Setup script for SmartOBD
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open("requirements.txt", "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            requirements.append(line)

setup(
    name="smartobd",
    version="1.0.0",
    author="SmartOBD Team",
    author_email="support@smartobd.com",
    description="Predictive Vehicle Maintenance Powered by OBD-II & AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/techdrivex/SmartOBD",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "smartobd=smartobd:main",
        ],
    },
    include_package_data=True,
    package_data={
        "smartobd": ["*.yaml", "*.yml", "*.json"],
    },
    keywords="obd obd2 vehicle maintenance prediction machine learning automotive",
    project_urls={
        "Bug Reports": "https://github.com/techdrivex/SmartOBD/issues",
        "Source": "https://github.com/techdrivex/SmartOBD",
        "Documentation": "https://github.com/techdrivex/SmartOBD/wiki",
    },
) 