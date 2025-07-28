# Initiative 2: Notion Integration and Document Processing

## Overview

This initiative implements a comprehensive Notion integration that allows users to:
1. Connect their Notion workspace
2. Browse and select documents for ingestion
3. Chunk and process documents efficiently
4. View and manage ingested documents via web interface
5. Search through documents using the new short-term memory system

## Architecture Design

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend UI                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Document Browser     Document Manager     Search Interface   │ │
│  │  - Browse Notion      - View ingested     - Search documents  │ │
│  │  - Select docs        - Manage chunks     - Filter by source   │ │
│  │  - Trigger ingestion  - Re-process        - View snippets     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│                              │ API Calls                          │
│                              ▼                                    │
└──────────────────────────────┼────────────────────────────────────┘
                              │
┌─────────────────────────────┼────────────────────────────────────┐
│                            Backend API                           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Notion Integration Service                  │ │
│  │                                                              │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌──────────────────┐   │ │
│  │  │OAuth Handler│ │Page Fetcher│ │Document Processor│   │ │
│  │  │- Connect    │ │- Get pages │ │- Clean content   │   │ │
│  │  │- Refresh    │ │- Get blocks│ │- Extract text    │   │ │
│  │  │- Manage     │ │- Pagination│ │- Handle media    │   │ │
│  │  └─────────────┘ └─────────────┘ └──────────────────┘   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│  ┌──────────────────────────────┴───────────────────────────────────┐ │
│  │                    Chunking Service                         │ │
│  │                                                              │ │
│  │  ┌─────────────────┐ ┌───────────────────────────────┐   │ │
│  │  │Semantic Chunker │ │  Memory Integration         │   │ │
│  │  │- Smart splits   │ │  - Short-term layer         │   │ │
│  │  │- Overlap        │ │  - Long-term sync           │   │ │
│  │  │- Metadata       │ │  - Document linking         │   │ │
│  │  └─────────────────┘ └───────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│                              ▼ Storage                            │
└─────────────────────────────┼────────────────────────────────────┘
                              │
 ┌────────────────────────────▼────────────────────────────────────┐
 │                    Document Storage System                       │
 │                                                                  │
 │  PostgreSQL              Short-term Layer        Long-term Layer│
 │  - Documents metadata    - FAISS + chunks        - Qdrant + Neo4j │
 │  - Chunking status       - Fast search           - Full analytics  │
 │  - Processing queue      - Immediate access      - Cross-device    │
 └──────────────────────────────────────────────────────────────────┘
```

## Prerequisites

**Depends on**: [INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md](./INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md)

Before starting this initiative, ensure the local development environment is set up with:
- Local database containers running
- Test data seeding capabilities
- Mock external service configurations
- Integration testing framework

## Implementation Plan

### Phase 1: Notion OAuth Integration

#### 1.1 OAuth Setup

```python
# app/integrations/notion/auth.py
from fastapi import APIRouter, Depends, HTTPException
from authlib.integrations.fastapi_oauth2 import OAuth2
from app.models import User, NotionIntegration

notion_oauth = OAuth2()
notion_oauth.register(
    name='notion',
    client_id=config.NOTION_CLIENT_ID,
    client_secret=config.NOTION_CLIENT_SECRET,
    server_metadata_url='https://api.notion.com/.well-known/oauth_authorization_server',
    client_kwargs={
        'scope': 'read'
    }
)

router = APIRouter(prefix="/integrations/notion", tags=["notion"])

@router.get("/connect")
async def connect_notion(user: User = Depends(get_current_user)):
    """Initiate Notion OAuth flow"""
    redirect_uri = f"{config.BASE_URL}/api/v1/integrations/notion/callback"
    return await notion_oauth.notion.authorize_redirect(
        redirect_uri=redirect_uri,
        state=user.id  # Pass user ID in state for callback
    )

@router.get("/callback")
async def notion_callback(
    code: str,
    state: str,  # user_id
    db: Session = Depends(get_db)
):
    """Handle Notion OAuth callback"""
    token = await notion_oauth.notion.authorize_access_token()
    
    # Get user info from Notion
    notion_user = await get_notion_user_info(token['access_token'])
    
    # Store integration
    integration = NotionIntegration(
        user_id=state,
        workspace_id=notion_user['workspace_id'],
        workspace_name=notion_user['workspace_name'],
        access_token=encrypt_token(token['access_token']),
        bot_id=notion_user['bot_id'],
        is_active=True
    )
    db.add(integration)
    db.commit()
    
    return {"status": "success", "workspace": notion_user['workspace_name']}
```

#### 1.2 Database Models

Refer to [JEAN_MEMORY_DATABASE_SCHEMA.md](./JEAN_MEMORY_DATABASE_SCHEMA.md) for base schema.

```sql
-- Additional tables for Notion integration
CREATE TABLE notion_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    workspace_id VARCHAR NOT NULL,
    workspace_name VARCHAR NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    bot_id VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notion_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID REFERENCES notion_integrations(id) NOT NULL,
    notion_page_id VARCHAR UNIQUE NOT NULL,
    title VARCHAR NOT NULL,
    url VARCHAR,
    parent_type VARCHAR,  -- 'database', 'page', 'workspace'
    parent_id VARCHAR,
    last_edited_time TIMESTAMP,
    is_selected BOOLEAN DEFAULT FALSE,
    is_processed BOOLEAN DEFAULT FALSE,
    content_hash VARCHAR,  -- To detect changes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE document_processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) NOT NULL,
    status VARCHAR DEFAULT 'pending',  -- pending, processing, completed, failed
    progress_percentage INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    processed_chunks INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Phase 2: Document Fetching and Processing

#### 2.1 Notion API Client

```python
# app/integrations/notion/client.py
from notion_client import Client
from typing import List, Dict, Any

class NotionClient:
    def __init__(self, access_token: str):
        self.client = Client(auth=access_token)
        
    async def get_pages(self, cursor: str = None) -> Dict[str, Any]:
        """Get all accessible pages"""
        kwargs = {"page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
            
        return self.client.search(**kwargs)
        
    async def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """Get full page content with blocks"""
        page = self.client.pages.retrieve(page_id)
        blocks = await self._get_all_blocks(page_id)
        
        return {
            "page": page,
            "blocks": blocks,
            "content": self._blocks_to_text(blocks)
        }
        
    async def _get_all_blocks(self, page_id: str, cursor: str = None) -> List[Dict]:
        """Recursively get all blocks from a page"""
        blocks = []
        
        response = self.client.blocks.children.list(
            block_id=page_id,
            start_cursor=cursor,
            page_size=100
        )
        
        blocks.extend(response['results'])
        
        # Handle pagination
        if response['has_more']:
            blocks.extend(
                await self._get_all_blocks(page_id, response['next_cursor'])
            )
            
        # Handle nested blocks
        for block in blocks:
            if block.get('has_children'):
                nested = await self._get_all_blocks(block['id'])
                block['children'] = nested
                
        return blocks
        
    def _blocks_to_text(self, blocks: List[Dict]) -> str:
        """Convert Notion blocks to clean text"""
        text_parts = []
        
        for block in blocks:
            block_type = block['type']
            
            if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3']:
                rich_text = block[block_type].get('rich_text', [])
                text = ''.join([t['plain_text'] for t in rich_text])
                if text.strip():
                    text_parts.append(text)
                    
            elif block_type == 'bulleted_list_item':
                rich_text = block[block_type].get('rich_text', [])
                text = ''.join([t['plain_text'] for t in rich_text])
                if text.strip():
                    text_parts.append(f"• {text}")
                    
            elif block_type == 'numbered_list_item':
                rich_text = block[block_type].get('rich_text', [])
                text = ''.join([t['plain_text'] for t in rich_text])
                if text.strip():
                    text_parts.append(f"1. {text}")
                    
            elif block_type == 'code':
                code_text = block[block_type]['rich_text']
                language = block[block_type].get('language', '')
                text = ''.join([t['plain_text'] for t in code_text])
                text_parts.append(f"```{language}\n{text}\n```")
                
            # Handle nested blocks
            if 'children' in block:
                nested_text = self._blocks_to_text(block['children'])
                if nested_text.strip():
                    text_parts.append(nested_text)
                    
        return '\n\n'.join(text_parts)
```

#### 2.2 Document Processing Service

```python
# app/services/document_processor.py
from typing import List, Dict
from app.services.chunking_service import SemanticChunker
from app.integrations.notion.client import NotionClient

class NotionDocumentProcessor:
    def __init__(self):
        self.chunker = SemanticChunker()
        
    async def process_selected_pages(
        self, 
        integration_id: str, 
        page_ids: List[str],
        user_id: str
    ) -> Dict[str, Any]:
        """Process selected Notion pages"""
        
        # Get integration details
        integration = await self._get_integration(integration_id)
        client = NotionClient(decrypt_token(integration.access_token))
        
        results = {
            "processed": 0,
            "failed": 0,
            "documents": [],
            "job_ids": []
        }
        
        for page_id in page_ids:
            try:
                # Create processing job
                job = await self._create_processing_job(page_id, user_id)
                results["job_ids"].append(str(job.id))
                
                # Process in background
                await self._queue_page_processing(client, page_id, job.id, user_id)
                results["processed"] += 1
                
            except Exception as e:
                logger.error(f"Failed to queue page {page_id}: {e}")
                results["failed"] += 1
                
        return results
        
    async def _queue_page_processing(
        self, 
        client: NotionClient, 
        page_id: str, 
        job_id: str,
        user_id: str
    ):
        """Queue page for background processing"""
        
        # Add to background task queue
        await background_tasks.add_task(
            "process_notion_page",
            client=client,
            page_id=page_id,
            job_id=job_id,
            user_id=user_id
        )
        
    async def process_page(
        self, 
        client: NotionClient, 
        page_id: str, 
        job_id: str,
        user_id: str
    ):
        """Process a single Notion page"""
        
        try:
            # Update job status
            await self._update_job_status(job_id, "processing")
            
            # Get page content
            page_data = await client.get_page_content(page_id)
            
            # Create document record
            document = await self._create_document(
                page_data=page_data,
                user_id=user_id,
                job_id=job_id
            )
            
            # Chunk the content
            chunks = await self.chunker.chunk_document(
                content=page_data['content'],
                document_id=document.id,
                metadata={
                    "source": "notion",
                    "page_id": page_id,
                    "title": page_data['page']['properties']['title']['title'][0]['plain_text'],
                    "url": page_data['page']['url']
                }
            )
            
            # Add to short-term memory immediately
            from app.utils.memory_layers import get_short_term_memory
            stm = get_short_term_memory(user_id)
            
            for chunk in chunks:
                await stm.add_document_chunk(
                    content=chunk['content'],
                    document_id=document.id,
                    chunk_index=chunk['index'],
                    metadata=chunk['metadata']
                )
                
            # Queue for long-term sync
            await self._queue_long_term_sync(document.id, chunks)
            
            # Update job completion
            await self._update_job_status(
                job_id, 
                "completed", 
                progress=100,
                total_chunks=len(chunks)
            )
            
        except Exception as e:
            logger.error(f"Failed to process page {page_id}: {e}")
            await self._update_job_status(job_id, "failed", error=str(e))
```

### Phase 3: Chunking Service Enhancement

#### 3.1 Semantic Chunking

Builds on existing chunking service from [JEAN_MEMORY_BACKEND_API.md](./JEAN_MEMORY_BACKEND_API.md).

```python
# app/services/chunking_service.py (Enhanced)
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticChunker:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    async def chunk_document(
        self, 
        content: str, 
        document_id: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Intelligently chunk document content"""
        
        # Basic text splitting
        basic_chunks = self.text_splitter.split_text(content)
        
        # Semantic enhancement
        enhanced_chunks = await self._enhance_chunks_semantically(basic_chunks)
        
        # Create chunk objects
        chunks = []
        for i, chunk_content in enumerate(enhanced_chunks):
            chunk = {
                "index": i,
                "content": chunk_content,
                "document_id": document_id,
                "metadata": {
                    **(metadata or {}),
                    "chunk_index": i,
                    "total_chunks": len(enhanced_chunks),
                    "word_count": len(chunk_content.split()),
                    "char_count": len(chunk_content)
                }
            }
            chunks.append(chunk)
            
        return chunks
        
    async def _enhance_chunks_semantically(
        self, 
        chunks: List[str]
    ) -> List[str]:
        """Use semantic similarity to optimize chunk boundaries"""
        
        if len(chunks) <= 1:
            return chunks
            
        # Get embeddings for all chunks
        embeddings = self.sentence_model.encode(chunks)
        
        # Calculate similarity between adjacent chunks
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = np.dot(embeddings[i], embeddings[i + 1]) / (
                np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i + 1])
            )
            similarities.append(sim)
            
        # Merge chunks with high similarity
        enhanced = []
        current_chunk = chunks[0]
        
        for i, similarity in enumerate(similarities):
            if similarity > 0.8 and len(current_chunk) + len(chunks[i + 1]) < 1500:
                # Merge with next chunk
                current_chunk += "\n\n" + chunks[i + 1]
            else:
                # Keep current chunk and start new one
                enhanced.append(current_chunk)
                current_chunk = chunks[i + 1]
                
        # Add the last chunk
        enhanced.append(current_chunk)
        
        return enhanced
```

### Phase 4: Frontend Implementation

Refer to [JEAN_MEMORY_FRONTEND.md](./JEAN_MEMORY_FRONTEND.md) for base frontend architecture.

#### 4.1 Document Browser Component

```typescript
// app/documents/page.tsx
"use client";

import { useState, useEffect } from 'react';
import { useNotionApi } from '@/hooks/useNotionApi';
import { DocumentBrowser } from '@/components/documents/DocumentBrowser';
import { DocumentManager } from '@/components/documents/DocumentManager';
import { ProcessingStatus } from '@/components/documents/ProcessingStatus';

export default function DocumentsPage() {
  const [activeTab, setActiveTab] = useState<'browse' | 'manage'>('browse');
  const { integration, isConnected } = useNotionApi();
  
  if (!isConnected) {
    return <NotionConnectionPrompt />;
  }
  
  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Documents</h1>
        <div className="flex gap-2">
          <Button 
            variant={activeTab === 'browse' ? 'default' : 'outline'}
            onClick={() => setActiveTab('browse')}
          >
            Browse Notion
          </Button>
          <Button 
            variant={activeTab === 'manage' ? 'default' : 'outline'}
            onClick={() => setActiveTab('manage')}
          >
            Manage Documents
          </Button>
        </div>
      </div>
      
      {activeTab === 'browse' ? (
        <DocumentBrowser integration={integration} />
      ) : (
        <DocumentManager />
      )}
      
      <ProcessingStatus />
    </div>
  );
}
```

#### 4.2 Document Browser

```typescript
// components/documents/DocumentBrowser.tsx
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Search, FileText, Database, Folder } from 'lucide-react';

interface NotionPage {
  id: string;
  title: string;
  url: string;
  parent_type: string;
  last_edited_time: string;
  is_selected: boolean;
  is_processed: boolean;
}

interface DocumentBrowserProps {
  integration: NotionIntegration;
}

export function DocumentBrowser({ integration }: DocumentBrowserProps) {
  const [pages, setPages] = useState<NotionPage[]>([]);
  const [selectedPages, setSelectedPages] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  useEffect(() => {
    loadPages();
  }, [integration.id]);
  
  const loadPages = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/integrations/notion/${integration.id}/pages`);
      const data = await response.json();
      setPages(data.pages);
    } catch (error) {
      console.error('Failed to load pages:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSelectPage = (pageId: string, checked: boolean) => {
    const newSelected = new Set(selectedPages);
    if (checked) {
      newSelected.add(pageId);
    } else {
      newSelected.delete(pageId);
    }
    setSelectedPages(newSelected);
  };
  
  const handleProcessSelected = async () => {
    if (selectedPages.size === 0) return;
    
    setIsProcessing(true);
    try {
      const response = await fetch(`/api/v1/integrations/notion/${integration.id}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          page_ids: Array.from(selectedPages)
        })
      });
      
      const result = await response.json();
      
      // Show success message and refresh
      toast.success(`Started processing ${result.processed} documents`);
      setSelectedPages(new Set());
      loadPages();
      
    } catch (error) {
      toast.error('Failed to start processing');
    } finally {
      setIsProcessing(false);
    }
  };
  
  const filteredPages = pages.filter(page => 
    page.title.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  const getPageIcon = (parentType: string) => {
    switch (parentType) {
      case 'database': return <Database className="w-4 h-4" />;
      case 'page': return <FileText className="w-4 h-4" />;
      default: return <Folder className="w-4 h-4" />;
    }
  };
  
  return (
    <div className="space-y-6">
      {/* Search and Actions */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search pages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button
          onClick={handleProcessSelected}
          disabled={selectedPages.size === 0 || isProcessing}
          loading={isProcessing}
        >
          Process Selected ({selectedPages.size})
        </Button>
      </div>
      
      {/* Pages List */}
      <div className="grid gap-4">
        {filteredPages.map((page) => (
          <Card key={page.id} className="transition-colors hover:bg-muted/50">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Checkbox
                  checked={selectedPages.has(page.id)}
                  onCheckedChange={(checked) => 
                    handleSelectPage(page.id, checked as boolean)
                  }
                  disabled={page.is_processed}
                />
                
                <div className="flex items-center gap-2">
                  {getPageIcon(page.parent_type)}
                  <span className="font-medium">{page.title}</span>
                </div>
                
                <div className="flex gap-2 ml-auto">
                  {page.is_processed && (
                    <Badge variant="secondary">Processed</Badge>
                  )}
                  <Badge variant="outline">
                    {new Date(page.last_edited_time).toLocaleDateString()}
                  </Badge>
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => window.open(page.url, '_blank')}
                >
                  View in Notion
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

### Phase 5: API Endpoints

#### 5.1 Notion Integration Routes

```python
# app/routers/notion_integration.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.integrations.notion.client import NotionClient
from app.services.document_processor import NotionDocumentProcessor

router = APIRouter(prefix="/integrations/notion", tags=["notion-integration"])

@router.get("/{integration_id}/pages")
async def get_notion_pages(
    integration_id: str,
    cursor: str = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pages from user's Notion workspace"""
    
    integration = db.query(NotionIntegration).filter(
        NotionIntegration.id == integration_id,
        NotionIntegration.user_id == user.id
    ).first()
    
    if not integration:
        raise HTTPException(404, "Integration not found")
        
    client = NotionClient(decrypt_token(integration.access_token))
    pages_data = await client.get_pages(cursor)
    
    # Store/update pages in database
    await sync_pages_to_db(integration.id, pages_data['results'], db)
    
    return {
        "pages": pages_data['results'],
        "has_more": pages_data['has_more'],
        "next_cursor": pages_data.get('next_cursor')
    }

@router.post("/{integration_id}/process")
async def process_notion_pages(
    integration_id: str,
    request: ProcessPagesRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """Process selected Notion pages"""
    
    processor = NotionDocumentProcessor()
    result = await processor.process_selected_pages(
        integration_id=integration_id,
        page_ids=request.page_ids,
        user_id=user.id
    )
    
    return result

@router.get("/processing-status")
async def get_processing_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status of all processing jobs"""
    
    jobs = db.query(DocumentProcessingJob).join(
        Document, DocumentProcessingJob.document_id == Document.id
    ).filter(
        Document.user_id == user.id
    ).order_by(DocumentProcessingJob.created_at.desc()).limit(50).all()
    
    return {"jobs": [job.to_dict() for job in jobs]}
```

## Integration with Short-term Memory

Builds on [INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md](./INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md).

```python
# Integration flow for documents
async def ingest_document_to_memory_layers(
    document_id: str, 
    chunks: List[Dict], 
    user_id: str
):
    """Ingest document chunks into both memory layers"""
    
    # 1. Add to short-term memory immediately (fast access)
    stm = get_short_term_memory(user_id)
    for chunk in chunks:
        await stm.add_document_chunk(
            content=chunk['content'],
            metadata={
                **chunk['metadata'],
                'document_id': document_id,
                'source': 'notion',
                'ingested_at': datetime.utcnow().isoformat()
            }
        )
    
    # 2. Queue for long-term memory sync (comprehensive storage)
    ltm_sync = get_memory_shuttle(user_id)
    await ltm_sync.queue_document_sync(document_id, chunks)
    
    return {
        'short_term_ingested': len(chunks),
        'long_term_queued': True
    }
```

## Performance Targets

- **Page fetching**: <2s for 100 pages
- **Document processing**: <30s per document
- **Chunk ingestion**: <1s per chunk to short-term memory
- **Search availability**: Immediate after short-term ingestion
- **Long-term sync**: <5 minutes background completion

## References

- [Local Development Setup](./INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md) - **Required prerequisite**
- [Backend API Documentation](./JEAN_MEMORY_BACKEND_API.md) - For service architecture
- [Frontend Architecture](./JEAN_MEMORY_FRONTEND.md) - For UI components
- [Database Schema](./JEAN_MEMORY_DATABASE_SCHEMA.md) - For data models
- [Short-term Memory System](./INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md) - For memory integration