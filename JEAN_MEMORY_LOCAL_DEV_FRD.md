# Jean Memory Local Development Environment - Mini-FRD

## **Part 1 — Mini-FRD (What & Why)**

### **1. What**
Create a `jean-memory-local-dev` repository that clones the main jean-memory codebase, transforms production-oriented files to local-friendly versions, and provides a complete local development environment with Docker-based services, multi-user account support, and production-equivalent user isolation for safe code testing and iteration.

### **2. Why**
Current development workflow forces blind production deployments causing frequent application breakdowns and development friction. This eliminates production risk by providing a completely isolated local environment where developers can test frontend/backend changes safely with multiple local user accounts before production deployment, enabling confident iteration, multi-user isolation testing, and team collaboration.

### **3. Scope**

**In Scope:**
- Automated cloning and transformation of jean-memory main repository
- File transformation system to convert production configs to local equivalents
- Docker Compose stack with all required services (PostgreSQL, Qdrant, Neo4j + APOC)
- Local JWT authentication service replacing Supabase auth bottlenecks
- Multi-user account creation and management within local environment
- Production-equivalent user isolation using mem0/graphiti user_id and group_id namespacing
- Local Qdrant collections per user (mimicking production structure)
- Local Neo4j graph data namespacing for multi-user testing
- Complete frontend + backend local testing environment
- LLM API key management for local development
- Local database seeding and migration support
- User account switching and testing workflows

**Out of Scope:**
- Any modifications to the main jean-memory production repository
- Production data access or migration from cloud services
- Shared development databases or centralized local services
- Production deployment or CI/CD pipeline changes
- Integration with existing Render/Supabase production infrastructure
- Cross-developer data sharing or collaboration features

### **4. Acceptance Criteria**
- [ ] Developer runs `git clone jean-memory-local-dev && cd jean-memory-local-dev && ./setup-local-dev.sh` successfully
- [ ] Transformed codebase starts without production dependencies (Supabase Cloud, Render URLs)
- [ ] Frontend at `localhost:3000` displays jean-memory UI with local data
- [ ] Backend API at `localhost:8000` responds to requests with local database
- [ ] Developer can create multiple local user accounts through local authentication service
- [ ] Each local user gets isolated Qdrant collection (e.g., `user_alice_memories`, `user_bob_memories`)
- [ ] Neo4j graph data properly namespaced using mem0/graphiti user_id isolation
- [ ] Developer can switch between local user accounts to test multi-user scenarios
- [ ] Local authentication works without Supabase CLI conflicts
- [ ] Neo4j runs with APOC plugins for mem0[graph] and graphiti-core compatibility
- [ ] Code changes in workspace reflect immediately in running local application
- [ ] Multi-user isolation functions identically to production (user data completely separated)
- [ ] Local environment completely isolated from production infrastructure

---

## **Implementation Architecture**

### **Multi-User Isolation Strategy**
```
Local Environment Structure:
├── PostgreSQL (users table + metadata)
├── Qdrant Collections:
│   ├── user_dev001_memories
│   ├── user_dev002_memories
│   └── user_dev003_memories
├── Neo4j (single graph with user_id namespacing)
└── Local Auth Service (JWT with user_id claims)
```

### **User Account Management**
- Local auth service provides user creation/login interface
- Each user gets unique user_id (dev001, dev002, etc.)
- mem0 and graphiti automatically namespace using these user_ids
- Developer can test user isolation by switching accounts

### **Production Parity**
- Qdrant collection naming matches production pattern
- mem0[graph] and graphiti user_id/group_id isolation preserved
- Graph data namespacing identical to production behavior
- Multi-user data separation testable locally

This approach enables comprehensive local testing of the multi-user jean-memory application while maintaining complete isolation from production infrastructure.