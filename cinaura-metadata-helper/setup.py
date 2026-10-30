"""Setup script for cinaura-metadata-helper."""

from setuptools import setup, find_packages

setup(
    name="cinaura-metadata-helper",
    version="1.0.0",
    description="Fetch TMDb metadata, NFO sidecars & artwork for Cinaura media libraries",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Cinaura Community",
    url="https://github.com/jrmux/cinaura-release",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "cinaura-metadata-helper=cinaura_metadata_helper.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
    ],
)

