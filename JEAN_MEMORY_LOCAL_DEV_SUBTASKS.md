# Jean Memory Local Development Environment - Subtasks & Mini-FRDs

## **PARENT TASK**
**Name:** Build Jean Memory Local Development Environment
**Category:** Backlog  
**Priority:** P2
**Description:** Create a complete local development environment that enables developers to clone, transform, and run the jean-memory application locally with multi-user support, eliminating blind production deployments and enabling safe code iteration with production-equivalent infrastructure.

---

## **SUBTASK 1: Create Repository Structure and Setup Scripts**

**Description:** Build the foundational repository structure and automated setup scripts for the jean-memory-local-dev environment, including Git automation, workspace creation, and prerequisite validation to enable one-command local environment initialization.

### **Mini-FRD (What & Why)**

#### **1. What**
Create the `jean-memory-local-dev` repository with automated setup scripts that clone the main jean-memory codebase and initialize the local development environment structure.

#### **2. Why**
Developers need a one-command setup experience to get started with local development. This eliminates manual configuration steps and ensures consistent environment setup across all developers.

#### **3. Scope**
**In Scope:**
- Repository creation with proper directory structure
- Main setup script (`setup-local-dev.sh`) for automated environment initialization
- Git clone automation for main jean-memory repository
- Developer workspace creation and isolation
- Prerequisites validation (Docker, Node.js, Python)
- Initial environment configuration file generation

**Out of Scope:**
- File transformations (handled in subtask 2)
- Service configuration (handled in subtask 4)
- Authentication setup (handled in subtask 3)

#### **4. Acceptance Criteria**
- [ ] Repository `jean-memory-local-dev` created with proper structure
- [ ] `./setup-local-dev.sh` clones main jean-memory repository successfully
- [ ] Script validates all prerequisites (Docker, Node.js, Python 3.12+)
- [ ] Creates isolated workspace directory for transformed code
- [ ] Generates initial `.env.local` configuration file
- [ ] Setup completes without manual intervention
- [ ] Clear error messages for missing prerequisites

---

## **SUBTASK 2: Build File Transformation System**

**Description:** Develop automated file transformation scripts that convert production-oriented code files (auth, config, database connections) from the main jean-memory repository into local-friendly versions that work with Docker containers and local services.

### **Mini-FRD (What & Why)**

#### **1. What**
Create a file transformation system that converts production-oriented files from the main jean-memory codebase into local-friendly versions suitable for development.

#### **2. Why**
Production code contains cloud service URLs, authentication flows, and deployment configurations that don't work locally. Automated transformation ensures local code works without manual editing while preserving production code integrity.

#### **3. Scope**
**In Scope:**
- Python-based transformation scripts for each file type
- Authentication file transformations (`auth.py`, `local_auth_helper.py`)
- Configuration file transformations (`settings.py`, `.env` files)
- Database connection string replacements
- Service URL replacements (Render → localhost)
- Environment variable overrides for local development
- Transformation validation and error handling

**Out of Scope:**
- Manual file editing or one-off transformations
- Production code modifications
- Runtime configuration changes

#### **4. Acceptance Criteria**
- [ ] Transformation scripts convert `auth.py` to use local JWT service
- [ ] `settings.py` forced to local development mode
- [ ] All Render URLs replaced with localhost equivalents
- [ ] Database URLs point to local containers
- [ ] Environment files generated with local service configurations
- [ ] Transformations are idempotent and repeatable
- [ ] Validation ensures all critical files are transformed correctly

---

## **SUBTASK 3: Implement Local Authentication Service**

**Description:** Create a standalone JWT authentication service to replace Supabase auth bottlenecks, supporting multi-user account creation, login/logout, session management, and seamless integration with the transformed jean-memory authentication flow.

### **Mini-FRD (What & Why)**

#### **1. What**
Build a local JWT authentication service that replaces Supabase auth and supports multi-user account creation, login, and session management for local development.

#### **2. Why**
Supabase CLI creates conflicts for multi-developer scenarios and doesn't support easy multi-user testing. A local auth service eliminates these bottlenecks while providing the same JWT-based authentication expected by the application.

#### **3. Scope**
**In Scope:**
- Standalone JWT authentication service (Python/FastAPI)
- User registration and login endpoints
- JWT token generation and validation
- Multi-user account support with unique user IDs
- Session management and token refresh
- User account switching interface
- Integration with transformed jean-memory auth code

**Out of Scope:**
- Production-level security features
- OAuth provider integrations
- Password complexity requirements
- Email verification flows

#### **4. Acceptance Criteria**
- [ ] Local auth service runs on dedicated port (e.g., 9999)
- [ ] Supports user registration with email/password
- [ ] Issues valid JWTs with user_id claims
- [ ] Multiple local users can be created and switched between
- [ ] JWTs integrate seamlessly with transformed auth.py
- [ ] User sessions persist across application restarts
- [ ] Simple web interface for user management

---

## **SUBTASK 4: Configure Docker Infrastructure Services**

**Description:** Set up Docker Compose configuration for all required local services (PostgreSQL, Qdrant, Neo4j with APOC plugins, Redis) with proper health checks, volume persistence, and port management to provide production-equivalent infrastructure locally.

### **Mini-FRD (What & Why)**

#### **1. What**
Create Docker Compose configuration for all required local services including PostgreSQL, Qdrant, Neo4j with APOC, and any other dependencies needed to run jean-memory locally.

#### **2. Why**
Local development requires the same database and service infrastructure as production. Docker ensures consistent service versions, easy setup, and isolation from host system configurations.

#### **3. Scope**
**In Scope:**
- Docker Compose configuration for all services
- PostgreSQL container with proper database initialization
- Qdrant container for vector storage
- Neo4j container with APOC plugins pre-installed
- Redis container for caching
- Service health checks and dependency management
- Volume persistence for development data
- Port management to avoid conflicts

**Out of Scope:**
- Production-level performance tuning
- High availability configurations
- Backup and recovery procedures
- Monitoring and alerting

#### **4. Acceptance Criteria**
- [ ] `docker-compose up` starts all required services
- [ ] PostgreSQL accessible with proper database and user setup
- [ ] Qdrant accessible and ready for vector operations
- [ ] Neo4j runs with APOC plugins for mem0[graph] and graphiti-core
- [ ] All services pass health checks
- [ ] Data persists between container restarts
- [ ] Services start in correct dependency order
- [ ] Clear error messages for Docker-related issues

---

## **SUBTASK 5: Build Multi-User Isolation System**

**Description:** Implement production-equivalent multi-user data isolation using Qdrant collections per user and Neo4j namespacing via mem0/graphiti user_id parameters, enabling local testing of user separation and data security features.

### **Mini-FRD (What & Why)**

#### **1. What**
Implement local multi-user isolation that mimics production behavior using Qdrant collections per user and Neo4j namespacing via mem0/graphiti user_id and group_id parameters.

#### **2. Why**
Production jean-memory relies on user isolation for data security and multi-tenancy. Local development must replicate this isolation to test user separation and ensure production parity.

#### **3. Scope**
**In Scope:**
- User-specific Qdrant collection creation and management
- Neo4j namespacing using mem0/graphiti user_id parameters
- Local user ID generation and assignment
- Data isolation validation and testing tools
- User switching workflows that maintain isolation
- Collection cleanup and management utilities

**Out of Scope:**
- Cross-user data sharing features
- User permission systems beyond basic isolation
- Data migration between users
- Production user data import

#### **4. Acceptance Criteria**
- [ ] Each local user gets isolated Qdrant collection (e.g., `user_dev001_memories`)
- [ ] Neo4j data properly namespaced using user_id from JWT
- [ ] User data completely isolated (no cross-user data leakage)
- [ ] User switching maintains proper data isolation
- [ ] mem0 and graphiti isolation functions identically to production
- [ ] Validation tools confirm isolation is working correctly
- [ ] Collection management handles user creation/deletion cleanly

---

## **SUBTASK 6: Create Development Workflow Tools**

**Description:** Build comprehensive developer tooling including environment management scripts, service monitoring, log aggregation, database utilities, and user management CLI to streamline local development workflows and debugging.

### **Mini-FRD (What & Why)**

#### **1. What**
Build development workflow tools including environment management scripts, testing utilities, and developer convenience features for efficient local development.

#### **2. Why**
Developers need tools to manage their local environment, switch configurations, test features, and debug issues. Good tooling accelerates development velocity and reduces friction.

#### **3. Scope**
**In Scope:**
- Environment start/stop/restart scripts
- Service status monitoring and health checks
- Log aggregation and viewing tools
- Database reset and seeding utilities
- User account management CLI
- Code change hot-reloading setup
- Development server management

**Out of Scope:**
- Production deployment tools
- Performance monitoring dashboards
- Automated testing frameworks
- Code quality enforcement tools

#### **4. Acceptance Criteria**
- [ ] `./start-dev.sh` starts entire local environment
- [ ] `./stop-dev.sh` cleanly stops all services
- [ ] Status commands show health of all services
- [ ] Log viewing tools for debugging issues
- [ ] Database reset utility for clean testing
- [ ] User management CLI for account operations
- [ ] Code changes reflect immediately in running application
- [ ] Clear documentation for all workflow commands

---

## **IMPLEMENTATION ORDER**

1. **Subtask 1** (Repository Structure) - Foundation for everything else
2. **Subtask 4** (Docker Infrastructure) - Services needed for testing transformations
3. **Subtask 3** (Local Auth Service) - Authentication needed before app can run
4. **Subtask 2** (File Transformation) - Core app transformation
5. **Subtask 5** (Multi-User Isolation) - Advanced feature testing
6. **Subtask 6** (Development Tools) - Quality of life improvements

Each subtask builds upon the previous ones, ensuring a logical development progression while enabling incremental testing and validation.