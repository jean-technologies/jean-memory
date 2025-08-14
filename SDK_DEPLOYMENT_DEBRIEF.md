# SDK Deployment Debrief & Next Steps

This document summarizes the deployment and testing of the Jean Memory SDKs (React, Node.js, Python) and outlines the critical issues found, with a plan to resolve them.

## What We Accomplished & Deployed

We successfully versioned and published three core SDK packages to their respective public registries.

-   **`@jeanmemory/react@1.0.3`** is live on npm.
-   **`@jeanmemory/node@1.0.1`** is live on npm.
-   **`jeanmemory==1.0.1`** is live on PyPI.

The version numbers in the local `package.json` and `setup.py` files were incremented, but these changes were **not** committed to the `main` branch.

## Core Problem Analysis: React SDK Build Failure

Despite multiple attempts, we were unable to get the `@jeanmemory/react` package working in a test Next.js application. The application consistently crashed with the following error:

```
TypeError: Cannot read properties of null (reading 'useState')
```

This error indicates that React hooks (like `useState`) were being called on the server, where they don't exist.

### Root Cause

The root cause is a build configuration issue with the React SDK's TypeScript compilation. The directive `'use client';`, which is required by Next.js to identify client-side components, was not being correctly placed at the very top of the compiled JavaScript files.

Our investigation revealed that the TypeScript compiler was adding `'use strict';` *before* `'use client';` in the final output, like so:

```javascript
"use strict";
'use client';
// ... rest of the code
```

This invalidates the `'use client';` directive, as Next.js requires it to be the absolute first line in the file.

### Failed Solutions

We attempted to solve this by:
1.  Adding `'use client';` to the source `.tsx` files.
2.  Creating a `post-build.js` script to manually correct the file headers in the `dist/` directory after compilation.

Neither of these solutions worked, which points to a deeper, more fundamental issue in how the TypeScript project is configured or how its output is being generated. The build process itself is likely flawed.

## The Path Forward

We need a fresh, robust approach that guarantees a correct build output from the start, rather than trying to patch it after the fact.

1.  **Adopt a Modern Build Tool:** The current setup using plain `tsc` is insufficient for building a modern React component library. We should replace it with a dedicated, industry-standard build tool like **Vite**, **esbuild**, or **Rollup**. These tools are explicitly designed for this purpose and have robust configurations to handle `'use client';` directives, tree-shaking, and multiple module formats (ESM, CJS) correctly. **Vite is the recommended choice** due to its speed and excellent defaults.

2.  **Re-scaffold the React SDK:** Start with a fresh template for a React component library. Vite, for example, has a template (`react-ts`) that can be adapted for this. This will give us a known-good `tsconfig.json`, `vite.config.ts`, and `package.json` setup.

3.  **Validate the Build Locally:** Before publishing, we must add a local validation step. This involves building the package and then linking it (`npm link`) to a local test application (like our `e2e-test-app`) to confirm it works *before* it ever touches the public npm registry.

4.  **Re-publish:** Once the build is validated locally, we will publish a new, working version (e.g., `1.1.0`).

This structured approach will eliminate the build issues and ensure the next deployment is a successful one.

---

## **Update:** Second Build Failure and Resolution

After implementing Vite, a new issue emerged during testing in a Next.js application:

```
Error: Failed to read source code from /.../sdk/react/dist/index.js
Caused by:
    No such file or directory (os error 2)
```

### Root Cause Analysis

This error occurred because the Vite build configuration was generating non-standard filenames (`index.es.js` and `index.umd.js`). While technically correct, many tools in the Node.js and React ecosystem have a "convention-over-configuration" expectation and are hardwired to look for specific files. The build process of the consuming application was still looking for a primary `dist/index.js` file, which no longer existed.

This points to an overly naive Vite configuration that didn't account for the conventions of the wider JavaScript ecosystem.

### The Refined Path Forward

To resolve this, we will adjust the Vite configuration to produce a more conventional and widely compatible package structure. This is the industry-standard approach for modern libraries.

1.  **Standardize Output Filenames:** The build will be reconfigured to output:
    *   `dist/index.js`: The CommonJS (CJS) or UMD build, for older tools and `require()`.
    *   `dist/index.mjs`: The ES Module (ESM) build, for modern bundlers and `import`.

2.  **Update `package.json` Entry Points:** The `main`, `module`, and `exports` fields will be updated to point to these new, standardized file paths. This ensures that both old and new build tools can correctly resolve the package entry points.

3.  **Final Validation:** After rebuilding, we will proceed with the local validation step to guarantee the fix before publishing.

This refined approach is much more robust and should resolve the file resolution errors permanently.

---

## **Update:** Third Build Failure & Final Resolution

Despite the previous fixes, the core runtime error persisted:

```
TypeError: Cannot read properties of null (reading 'useState')
```

### Final Root Cause Analysis

This error, occurring during server-side rendering, indicates that the React library itself is `null` when the SDK's code is executed by the Next.js server. The investigation revealed that the issue was the module format of the build output.

The previous build generated a UMD (`Universal Module Definition`) file for the `require` entry point. While designed for universal compatibility, the UMD format's environment detection can be unreliable in a modern SSR framework like Next.js. The server was failing to correctly resolve the `react` peer dependency within the UMD wrapper, leading to the crash.

The optimization goal is **robust ecosystem compatibility**, especially with modern, server-rendered frameworks. The SDK must "just work" without forcing consumers to add workarounds.

### The Definitive Fix

The solution is to abandon the UMD format in favor of outputs specifically tailored for their target environments.

1.  **Switch to CJS for the Main Entry:** The build process will be changed to generate a CommonJS (`.cjs`) file instead of a UMD file. CJS is the native module format for Node.js, which is the environment used by the Next.js server. This guarantees correct module resolution.

2.  **Maintain ESM for the Module Entry:** The ES Module (`.mjs`) build will be kept, as it is the standard for modern frontend bundlers (like Vite and Webpack) and enables features like tree-shaking.

3.  **Update `package.json`:** The `main` and `exports.require` fields will be updated to point to `dist/index.cjs`.

This configuration provides distinct, purpose-built modules for the server (`.cjs`) and the client (`.mjs`), which is the industry-standard best practice for building modern, SSR-compatible libraries. This resolves the underlying module resolution conflict and eliminates the runtime error.
