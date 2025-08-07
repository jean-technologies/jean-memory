# TODO: Automate Documentation Generation

This file is a placeholder to track the necessary work to automate the documentation generation process.

The current process is manual and requires a developer to run `python3 scripts/create_consolidated_docs.py` and commit the result.

## Action Items

1.  **Modify the `cd.yml` workflow** to be triggered on pushes to the `main` branch, specifically when files in `docs-mintlify/` are changed.
2.  **Add a new job** to this workflow that runs the `create_consolidated_docs.py` script.
3.  **Add a step to the job** that commits the updated `docs-mintlify/assets/consolidated-docs.md` file back to the `main` branch.

This will ensure the documentation is always in sync with the source files without manual intervention.
