# How to Update Documentation

This directory contains the source files for our documentation, which is hosted on Mintlify. The documentation served to users in the "Copy All Docs" button is a single, consolidated file.

**This process is currently MANUAL.**

## To Update the Documentation:

Follow these two steps **every time** you add, remove, or change a documentation file.

### Step 1: Regenerate the Consolidated File

Run the following command from the root of the project to regenerate the master documentation file (`assets/consolidated-docs.md`).

```bash
python3 scripts/create_consolidated_docs.py
```

This script will automatically find all `.mdx` files and bundle them together. You do not need to edit the script.

### Step 2: Commit and Push the Changes

Commit the updated `assets/consolidated-docs.md` file and push it to the main branch.

```bash
git add docs-mintlify/assets/consolidated-docs.md
git commit -m "docs: update consolidated documentation"
git push
```

After you push, Mintlify/Vercel will automatically redeploy the documentation site with your changes.
