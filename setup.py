#!/usr/bin/env python
"""Setup script for agentic-context-engine."""

from setuptools import setup, find_packages

# Read the README file for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Read optional requirements
try:
    with open("requirements-optional.txt", "r", encoding="utf-8") as fh:
        optional_requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    optional_requirements = []

setup(
    name="ac-engine",
    version="0.1.0",
    author="Kayba.ai",
    author_email="hello@kayba.ai",
    description="Build self-improving AI agents that learn from experience",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Kayba-ai/ace-framework",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "all": optional_requirements,
        "litellm": ["litellm>=1.0.0"],
        "transformers": ["transformers>=4.0.0", "torch>=2.0.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
)