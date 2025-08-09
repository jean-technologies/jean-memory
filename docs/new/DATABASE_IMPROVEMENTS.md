# Database Schema Issues & Improvements

## 🔴 Critical Issues (Fix Immediately)

### 1. **Phone/SMS Fields Schema Mismatch**
- **Problem**: Migration `6a4b2e8f5c91` adds phone fields as columns but User model stores them in metadata JSON
- **Fields affected**: `phone_number`, `phone_verified`, `phone_verification_attempts`, `phone_verified_at`, `sms_enabled`
- **Fix**: Add these columns to User model (like we just did with firstname/lastname)
```python
# Add to User model:
phone_number = Column(String(20), nullable=True, unique=True, index=True)
phone_verified = Column(Boolean, default=False, nullable=True)
phone_verification_attempts = Column(Integer, default=0, nullable=True)
phone_verified_at = Column(DateTime, nullable=True)
sms_enabled = Column(Boolean, default=True, nullable=True)
```

### 2. **Orphaned Tables Not in Models**
- **Problem**: Tables exist in DB but not in models.py
- `claude_code_sessions` and `claude_code_agents` - Created by SQL scripts but no SQLAlchemy models
- `memories_backup_66d3d5d1` - Old backup table still in production
- `user_integrations_backup` - Another backup table
- **Fix**: Either create proper models or drop these tables

### 3. **Inconsistent UUID Types**
- **Problem**: Mixed UUID column definitions
- Some use `UUID` directly: `id = Column(UUID, primary_key=True, default=lambda: uuid.uuid4())`
- Others use `UUID(as_uuid=True)`: `id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`
- **Fix**: Standardize to `UUID(as_uuid=True)` for all UUID columns

## 🟡 Major Inconsistencies

### 1. **Naming Convention Issues**
- `metadata_` mapped to `metadata` column (good)
- But inconsistent timezone handling in DateTime columns:
  - Some use `DateTime(timezone=True)` 
  - Others use plain `DateTime`
- Foreign key naming: some use `owner_id`, others use `user_id` for same purpose

### 2. **SubscriptionTier Enum vs String**
- **Problem**: `SubscriptionTier` enum defined but not used
- User model uses `String(10)` for subscription_tier
- Migration `3d72586d0607` suggests previous enum issues
- **Current state**: Working but inconsistent

### 3. **Duplicate Indexes**
- ApiKey table has redundant index:
  - `user_id` column already has `index=True`
  - Also has `Index('idx_apikey_user_id', 'user_id')`

## 🟠 Design Issues

### 1. **Missing Relationships**
- ApiKey has no back_populates on User model
- MemoryStatusHistory and MemoryAccessLog have no relationships defined

### 2. **Inefficient JSON Storage**
- Heavy use of JSON/JSONB for structured data (metadata fields)
- Phone fields stored in metadata when they should be columns
- Consider extracting frequently queried fields

### 3. **Missing Constraints**
- No check constraints on string lengths (except firstname/lastname)
- No validation on sync_status values (should be enum)
- Missing foreign key cascades in some places

### 4. **Poor Event Listener Implementation**
- `categorize_memory` runs synchronously on every insert/update
- This makes writes slow and can fail silently
- Should be async or queued

## 🟢 Recommendations

### Immediate Actions:
1. **Fix phone fields** - Add columns to User model, migrate data from metadata
2. **Clean up backup tables** - Drop `memories_backup_66d3d5d1` and `user_integrations_backup`
3. **Standardize UUID types** - Use `UUID(as_uuid=True)` everywhere

### Short-term Improvements:
1. **Add proper models for claude_code tables** or move them to separate DB
2. **Fix DateTime timezone consistency** - All should be `DateTime(timezone=True)`
3. **Add missing relationships and cascades**
4. **Create migration to extract phone fields from metadata to columns**

### Long-term Improvements:
1. **Async categorization** - Move to background job queue
2. **Optimize metadata usage** - Extract frequently queried fields to columns
3. **Add proper enums** for status fields (sync_status, subscription_status)
4. **Data validation** - Add check constraints and validators

## 📊 Table-Specific Issues

### Users Table
- ✅ firstname/lastname fixed (just now)
- ❌ Phone fields still in metadata
- ❌ Missing relationship to ApiKey

### Apps Table
- ❌ sync_status should be enum not string
- ⚠️ sync_error as Text might be too large

### Memories Table
- ❌ vector as String is inefficient (should use pgvector)
- ⚠️ Heavy trigger load from categorization

### Document/DocumentChunk
- ✅ Properly uses JSONB for metadata
- ✅ Has proper cascade delete
- ⚠️ embedding as ARRAY(Float) - consider pgvector

### SMSConversation
- ✅ Proper enum for role
- ✅ Good indexing

## 🗑️ Tables to Remove
1. `memories_backup_66d3d5d1` - Old backup from September
2. `user_integrations_backup` - Unused backup
3. Consider moving `claude_code_*` tables to separate coordination DB

## 🔧 Model Code Issues

The models.py file has several issues:
1. **Mixed import styles** - Both `from enum import Enum as PyEnum` and `import enum`
2. **Inefficient event listeners** - Synchronous categorization on every memory
3. **Hardcoded PostgreSQL logic** - Grant permissions only works for PostgreSQL
4. **No proper base class methods** - Could add common methods to Base

## Priority Order:
1. Fix phone fields schema mismatch (CRITICAL)
2. Drop backup tables (EASY)
3. Standardize UUID and DateTime types (MEDIUM)
4. Fix missing relationships (MEDIUM)
5. Move categorization to async (COMPLEX)