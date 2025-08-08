# SDK Publishing Scripts

This directory contains automated scripts for publishing Jean Memory SDKs to their respective package registries.

## Available Scripts

### `publish-python.sh`
Publishes the Python SDK to PyPI as `jeanmemory`
- Cleans previous builds
- Uses modern Python build tools (`python3 -m build`)
- Validates package with twine
- Publishes to PyPI

### `publish-node.sh`
Publishes the Node.js SDK to NPM as `jeanmemory-node`
- Installs dependencies
- Compiles TypeScript
- Validates build output
- Publishes to NPM with public access

### `publish-all.sh`
Convenience script that publishes both Python and Node.js SDKs
- Runs both publish scripts sequentially
- Provides installation commands for all SDKs
- Notes about React SDK (published separately)

## Usage

```bash
# Publish individual SDKs
cd jean-memory/sdk/scripts
./publish-python.sh
./publish-node.sh

# Publish all SDKs at once
./publish-all.sh
```

## Prerequisites

- Python 3.10+ with `build` and `twine` installed
- Node.js 18+ with NPM configured
- Valid PyPI and NPM credentials
- Proper version numbers in package.json and setup.py

## Current Published Packages

- **Python**: `pip install jeanmemory`
- **Node.js**: `npm install jeanmemory-node` 
- **React**: `npm install jeanmemory-react`