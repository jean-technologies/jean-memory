"""
Jean Memory Python SDK Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="jeanmemory",
    version="1.4.2",
    author="Jean Memory",
    author_email="support@jeanmemory.com",
    description="Python SDK for Jean Memory - Add long-term memory to your Python agents and backend services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jean-technologies/jean-memory",
    project_urls={
        "Bug Tracker": "https://github.com/jean-technologies/jean-memory/issues",
        "Documentation": "https://jeanmemory.com/docs",
        "Homepage": "https://jeanmemory.com",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    packages=["jean_memory"],
    py_modules=["jeanmemory"],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "openai": ["openai>=1.0.0"],
    },
    keywords="jean-memory ai chatbot personalization sdk",
)