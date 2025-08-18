# Jean Memory SDK Testing - Notion/JIRA Tasks with FRD/EDD

## 🎯 **TESTING STRATEGY: Published Package First**

### **Current Published Versions:**
- **React SDK:** v1.2.1 (NPM) 
- **Python SDK:** v1.2.4 (PyPI)
- **Node.js SDK:** v1.2.4 (NPM)

### **Testing Approach:**
**Test published packages directly** → **Fix if needed** → **Republish with new version**

This ensures we test exactly what developers install, not what's in our repository.

---

## Task 1: React SDK Validation & Enhancement

### **Task Name:**
`[SDK] Validate React SDK v1.2.1 - Test UI Components & Developer Experience`

### **Task Description:**
**Objective:** Validate the recently published React SDK v1.2.1 to ensure all documented features work correctly and the new "crisp" UI meets quality standards.

**Priority:** P0
**Estimated Time:** 8 hours
**Labels:** `sdk`, `react`, `testing`, `documentation`

### **FRD/EDD**

#### **Part 1 — Mini-FRD (What & Why)**

1. **What**  
   Validate the React SDK v1.2.1 to ensure the 5-line integration works perfectly, test the new clean UI design, and verify all exports match documentation.

2. **Why**  
   SDK was just published with major UI improvements ("crisp like ChatBase") and needs validation. Documentation examples must be tested to ensure developer success. This is the primary SDK for frontend developers.

3. **Scope**  
   
   **In Scope:**
   - Test 5-line integration from docs
   - Validate JeanProvider, JeanChat, useJean exports
   - Test SignInWithJean authentication flow
   - Verify new clean UI design quality
   - Test useJeanMCP for advanced users
   - Validate TypeScript type definitions
   - Test all documentation examples
   
   **Out of Scope:**
   - Backend API changes
   - New feature development
   - OAuth provider modifications
   - Further UI redesign

4. **Acceptance Criteria**
   - [ ] `npm install @jeanmemory/react@1.2.1` works cleanly
   - [ ] 5-line integration from docs works perfectly
   - [ ] JeanProvider wraps app without errors
   - [ ] JeanChat renders with clean, professional UI
   - [ ] useJean hook returns all documented methods
   - [ ] SignInWithJean authenticates successfully
   - [ ] TypeScript types properly exported
   - [ ] All documentation examples execute correctly

#### **Part 2 — Mini-EDD (How)**

**Technical Approach:**
1. Create fresh Next.js/React app
2. Install **@jeanmemory/react@1.2.1 from NPM** (published package)
3. Test 5-line integration from documentation
4. If issues found: Download package, fix locally, test fixes
5. If fixes work: Republish as v1.2.2

**Published Package Testing:**
- Test exactly what developers get: `npm install @jeanmemory/react@1.2.1`
- Run all documentation examples
- Identify gaps between docs and package

**Fix & Republish Workflow:**
1. Download: `npm pack @jeanmemory/react@1.2.1`
2. Extract and fix issues locally
3. Test fixed version thoroughly
4. Update repository code to match fixes
5. Republish as new version (v1.2.2)

---

## Task 2: Python SDK Documentation & Import Testing

### **Task Name:**
`[SDK] Validate Python SDK v1.2.3 - Test Corrected Documentation & Import Structure`

### **Task Description:**
**Objective:** Validate the Python SDK v1.2.3 to ensure the corrected documentation works and the jean_memory import structure functions properly.

**Priority:** P0
**Estimated Time:** 6 hours
**Labels:** `sdk`, `python`, `testing`, `backend`

### **FRD/EDD**

#### **Part 1 — Mini-FRD (What & Why)**

1. **What**  
   Validate Python SDK v1.2.3 to ensure the corrected import structure (`from jean_memory import JeanClient`) works and all documentation examples execute properly.

2. **Why**  
   Documentation was recently fixed to use correct import statements. Previous docs showed non-working imports. Package structure needs validation to ensure developers can successfully integrate.

3. **Scope**  
   
   **In Scope:**
   - Test pip installation of jeanmemory==1.2.3
   - Validate jean_memory module imports
   - Test JeanClient initialization
   - Verify get_context() method
   - Test OAuth token authentication
   - Validate Python 3.8-3.12 compatibility
   - Test all documentation examples
   
   **Out of Scope:**
   - New AI model integrations
   - Backend API modifications
   - Memory storage changes
   - OpenAI integration (now optional)

4. **Acceptance Criteria**
   - [ ] `pip install jeanmemory==1.2.3` installs successfully
   - [ ] `from jean_memory import JeanClient` works
   - [ ] JeanClient initializes with API key
   - [ ] get_context() returns expected format
   - [ ] OAuth token authentication works
   - [ ] Works with Python 3.8+
   - [ ] All documentation examples execute
   - [ ] Optional OpenAI dependency documented

#### **Part 2 — Mini-EDD (How)**

**Technical Approach:**
1. Create fresh Python virtual environment
2. Install **jeanmemory==1.2.4 from PyPI** (published package)
3. Test import statements from documentation
4. If issues found: Download package, fix locally, test fixes
5. If fixes work: Republish as v1.2.5

**Published Package Testing:**
- Test exactly what developers get: `pip install jeanmemory==1.2.4`
- Test import: `from jean_memory import JeanClient`
- Run all documentation examples
- Identify import/structure issues

**Fix & Republish Workflow:**
1. Download: `pip download jeanmemory==1.2.4`
2. Extract, fix import issues locally
3. Test fixed version in clean environment
4. Update repository structure to match fixes
5. Republish as new version (v1.2.5)

---

## Task 3: Node.js SDK Integration Testing

### **Task Name:**
`[SDK] Validate Node.js SDK v1.2.4 - Test Next.js Integration & Authentication Flow`

### **Task Description:**
**Objective:** Validate the Node.js SDK v1.2.4 for seamless Next.js integration, test the auto test user functionality, and verify edge runtime compatibility.

**Priority:** P0
**Estimated Time:** 6 hours
**Labels:** `sdk`, `nodejs`, `testing`, `nextjs`, `serverless`

### **FRD/EDD**

#### **Part 1 — Mini-FRD (What & Why)**

1. **What**  
   Validate Node.js SDK v1.2.4 to ensure Next.js integration works, test the auto test user functionality for development, and verify all exports function correctly.

2. **Why**  
   SDK was recently updated to v1.2.4 with auto test user functionality. Need to validate that Next.js integration works seamlessly and authentication flows are properly implemented.

3. **Scope**  
   
   **In Scope:**
   - Test npm installation @jeanmemory/node@1.2.4
   - Validate JeanClient initialization
   - Test getContext() method functionality
   - Test auto test user feature for development
   - Verify Next.js API route integration
   - Test edge runtime compatibility
   - Validate TypeScript exports
   
   **Out of Scope:**
   - Frontend components
   - OAuth provider setup
   - WebSocket implementation
   - Database schema changes

4. **Acceptance Criteria**
   - [ ] `npm install @jeanmemory/node@1.2.4` works
   - [ ] JeanClient initializes with API key
   - [ ] getContext() returns proper response
   - [ ] Auto test user creates isolated users
   - [ ] Next.js API route examples work
   - [ ] Edge runtime compatibility verified
   - [ ] All TypeScript types exported
   - [ ] Documentation examples execute

#### **Part 2 — Mini-EDD (How)**

**Technical Approach:**
1. Create fresh Next.js 14+ app
2. Install **@jeanmemory/node@1.2.4 from NPM** (published package)
3. Test Next.js API route integration from documentation
4. If issues found: Download package, fix locally, test fixes
5. If fixes work: Republish as v1.2.5

**Published Package Testing:**
- Test exactly what developers get: `npm install @jeanmemory/node@1.2.4`
- Test imports: `import { JeanClient } from '@jeanmemory/node'`
- Run all documentation examples
- Test auto test user functionality

**Fix & Republish Workflow:**
1. Download: `npm pack @jeanmemory/node@1.2.4`
2. Extract, fix issues locally
3. Test fixed version in Next.js app
4. Update repository code to match fixes
5. Republish as new version (v1.2.5)

---

## Epic/Parent Task

### **Epic Name:**
`[EPIC] SDK Validation Suite - Verify Published SDKs v1.2.x`

### **Epic Description:**
**Objective:** Validate all recently published Jean Memory SDKs (React v1.2.1, Python v1.2.3, Node.js v1.2.4) to ensure production readiness and documentation accuracy.

### **FRD/EDD**

#### **Part 1 — Mini-FRD (What & Why)**

1. **What**  
   Comprehensive validation of all three recently published Jean Memory SDKs to ensure they work as documented and provide excellent developer experience.

2. **Why**  
   SDKs were recently published with major improvements (UI redesign, documentation fixes, new features). Need validation to ensure all changes work correctly and developers can successfully integrate.

3. **Scope**  
   
   **In Scope:**
   - Validate all published packages install correctly
   - Test documentation examples execute properly
   - Verify UI improvements meet quality standards
   - Test cross-SDK compatibility (React + Node.js)
   - Validate TypeScript types and exports
   - Test authentication flows
   
   **Out of Scope:**
   - New SDK development
   - Backend API changes
   - Breaking changes to existing APIs
   - Additional feature development

4. **Acceptance Criteria**
   - [ ] All SDKs install without warnings
   - [ ] 100% of documentation examples work
   - [ ] React UI meets "crisp like ChatBase" standard
   - [ ] Python imports work correctly
   - [ ] Node.js auto test user functionality works
   - [ ] Cross-SDK integration functional
   - [ ] Developer integration < 5 minutes

#### **Part 2 — Mini-EDD (How)**

**Technical Approach:**
1. Create fresh test environments for each SDK
2. Install **published packages directly** from NPM/PyPI
3. Test all documentation examples against published packages
4. Fix issues locally and test fixes
5. Republish improved versions if needed

**Published Package First Strategy:**
- React: `npm install @jeanmemory/react@1.2.1`
- Python: `pip install jeanmemory==1.2.4`  
- Node.js: `npm install @jeanmemory/node@1.2.4`

**Success Metrics:**
- All published packages work as documented
- Zero gaps between docs and published packages
- Cross-SDK integration functional
- If fixes needed: New versions published and tested

**Timeline:** 1 Sprint (2 weeks)
**Priority:** High
**Labels:** `epic`, `sdk`, `validation`, `q1-2025`