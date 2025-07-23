# Jean Memory V2 - Repository Setup Guide

## Phase 1: Creating the Separate Repository

### Step 1: Create New GitHub Repository

1. Go to GitHub and create a new repository named `jean-memory-v2`
2. Make it **public** (for git+https installation to work easily)
3. Initialize with README (you'll replace it)

### Step 2: Clone and Setup New Repository

```bash
# Clone the new empty repository
git clone https://github.com/jonathan-politzki/jean-memory-v2.git
cd jean-memory-v2

# Copy all jean_memory_v2 contents from your-memory repo
cp -r /path/to/your-memory/jean_memory_v2/* .

# Remove any local references that won't work in standalone repo
# (These will be handled during testing)
```

### Step 3: Initial Commit

```bash
git add .
git commit -m "Initial commit: Jean Memory V2 standalone library

- Add complete jean_memory_v2 library code
- Add pyproject.toml and setup.py for pip installation  
- Add LICENSE and MANIFEST.in
- Ready for git+https pip installation"

git push origin main
```

## Step 4: Test Installation

Test the git+https installation:

```bash
# From your-memory project or a test environment
pip install git+https://github.com/jonathan-politzki/jean-memory-v2.git

# Test import
python -c "from jean_memory_v2 import JeanMemoryV2; print('✅ Installation successful!')"
```

## Step 5: Update your-memory Repository

Once the separate repository is working, update your main project:

### Update requirements.txt

In `openmemory/api/requirements.txt`, add:
```
# Jean Memory V2 - Separate Repository
jean-memory-v2 @ git+https://github.com/jonathan-politzki/jean-memory-v2.git
```

### Update imports (no changes needed)

The imports in your code should work the same:
```python
# These imports will work unchanged
from jean_memory_v2.mem0_adapter_optimized import get_memory_client_v2_optimized
from jean_memory_v2.config import JeanMemoryConfig
```

### Remove local jean_memory_v2 folder

After confirming everything works:
```bash
# In your-memory repository
rm -rf jean_memory_v2/
git add -A
git commit -m "Remove local jean_memory_v2 - now using separate repository

jean_memory_v2 is now installed via:
pip install git+https://github.com/jonathan-politzki/jean-memory-v2.git"
git push
```

## Benefits Achieved

✅ **Isolated Development**: jean_memory_v2 can be developed and versioned independently  
✅ **Reusable Library**: Can be used in other projects  
✅ **Cleaner Architecture**: Separation of concerns  
✅ **Better CI/CD**: Each repo can have its own testing and deployment  
✅ **Version Management**: Can tag releases and manage versions properly

## Next Steps After This Works

1. **Add CI/CD** to jean-memory-v2 repository
2. **Add comprehensive tests** in the new repo
3. **Version tagging** for stable releases
4. **Consider PyPI publishing** for public availability
5. **Phase 2**: Flatten openmemory folder structure in main repo

## Troubleshooting

If installation fails:
1. Ensure repository is public
2. Check that all Python files are properly formatted
3. Verify pyproject.toml syntax
4. Test local installation with `pip install -e .` in the jean-memory-v2 directory