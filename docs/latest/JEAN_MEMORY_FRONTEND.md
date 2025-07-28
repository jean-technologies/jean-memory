# Jean Memory Frontend Architecture

## Overview

The Jean Memory frontend is a modern Next.js application built with React 18, TypeScript, and Tailwind CSS. It provides a responsive, real-time interface for managing personal memories across multiple AI applications.

## Technology Stack

- **Framework**: Next.js 15.2.4 (App Router)
- **UI Library**: React 18
- **Language**: TypeScript
- **Styling**: Tailwind CSS + CSS Modules
- **UI Components**: Radix UI + shadcn/ui
- **State Management**: Redux Toolkit
- **Authentication**: Supabase Auth
- **API Client**: Axios
- **Forms**: React Hook Form + Zod
- **Real-time**: Supabase Realtime
- **Analytics**: PostHog
- **Package Manager**: pnpm

## Project Structure

```
openmemory/ui/
├── app/                         # Next.js App Router
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Landing page
│   ├── auth/                    # Authentication pages
│   │   ├── page.tsx             # Login/Signup
│   │   └── callback/page.tsx   # OAuth callback
│   ├── dashboard/               # Main dashboard
│   │   ├── page.tsx             # Dashboard home
│   │   └── layout.tsx           # Dashboard layout
│   ├── memories/                # Memory management
│   │   ├── page.tsx             # Memory list
│   │   └── components/          # Memory components
│   ├── memory/[id]/             # Memory detail
│   ├── apps/                    # App management
│   │   ├── page.tsx             # App list
│   │   └── [appId]/page.tsx    # App detail
│   ├── my-life/                 # Knowledge graph
│   ├── settings/                # User settings
│   └── api/                     # API routes
│       ├── chat/route.ts        # Chat endpoint
│       └── narrative/route.ts   # Narrative generation
├── components/                  # Shared components
│   ├── ui/                      # Base UI components
│   ├── dashboard/               # Dashboard components
│   ├── auth/                    # Auth components
│   ├── memory-v3/               # Memory v3 components
│   └── shared/                  # Shared utilities
├── contexts/                    # React contexts
│   ├── AuthContext.tsx          # Authentication
│   └── ThemeContext.tsx         # Theme management
├── hooks/                       # Custom React hooks
│   ├── useMemoriesApi.ts        # Memory API hooks
│   ├── useAppsApi.ts            # Apps API hooks
│   ├── useProfile.ts            # User profile hook
│   └── useStats.ts              # Statistics hook
├── lib/                         # Utility libraries
│   ├── supabaseClient.ts        # Supabase client
│   ├── apiClient.ts             # API client setup
│   ├── utils.ts                 # General utilities
│   └── memory-v3/               # Memory v3 lib
├── store/                       # Redux store
│   ├── store.ts                 # Store configuration
│   ├── memoriesSlice.ts         # Memories state
│   ├── appsSlice.ts             # Apps state
│   ├── profileSlice.ts          # Profile state
│   └── uiSlice.ts               # UI state
└── public/                      # Static assets
    └── images/                  # Images and icons
```

## Key Features

### 1. Authentication System

**AuthContext (`contexts/AuthContext.tsx`)**
- Manages authentication state globally
- Supports multiple auth methods:
  - Email/Password
  - Google OAuth
  - GitHub OAuth
- Handles JWT token management
- Integrates with PostHog for analytics

**Protected Routes**
- `ProtectedRoute` component wraps authenticated pages
- Automatic redirect to login for unauthenticated users
- Session persistence across page reloads

### 2. Dashboard

**Main Dashboard (`app/dashboard/page.tsx`)**
- Displays connected apps with real-time status
- App installation modal with MCP commands
- Memory statistics and analytics
- Quick actions for common tasks
- Profile completion prompts

**Key Components:**
- `AppCard`: Display connected app info
- `InstallModal`: MCP installation instructions
- `SyncModal`: App synchronization UI
- `AnalysisPanel`: Memory analytics

### 3. Memory Management

**Memory List (`app/memories/page.tsx`)**
- Paginated memory display
- Advanced filtering:
  - Date range
  - Categories
  - Apps
  - Search query
- Bulk operations (delete, pause)
- Real-time updates

**Memory Components:**
- `MemoryTable`: Tabular memory display
- `MemoryFilters`: Filter controls
- `CreateMemoryDialog`: Add new memory
- `DeepQueryDialog`: AI-powered search

### 4. Knowledge Graph

**My Life View (`app/my-life/page.tsx`)**
- Interactive 3D knowledge graph
- Relationship visualization
- Entity exploration
- Timeline view
- Chat interface for queries

**Visualization Libraries:**
- Three.js for 3D rendering
- Cytoscape.js for graph layouts
- D3.js for custom visualizations

### 5. App Integration

**Apps Management (`app/apps/page.tsx`)**
- List of available integrations
- Connection status indicators
- One-click installation for supported apps
- Custom MCP connection instructions

**Supported Apps:**
- ChatGPT (via custom GPT)
- Claude (Desktop extension)
- VS Code / Cursor
- SMS (Twilio integration)
- Substack / Twitter sync
- Generic MCP connections

## State Management

### Redux Store Structure

```typescript
interface RootState {
  memories: {
    memories: Memory[]
    totalMemories: number
    isLoading: boolean
    error: string | null
  }
  apps: {
    apps: App[]
    selectedApp: App | null
    isLoading: boolean
  }
  profile: {
    userId: string | null
    profile: UserProfile | null
    stats: UserStats | null
  }
  ui: {
    sidebarOpen: boolean
    theme: 'light' | 'dark' | 'system'
    notifications: Notification[]
  }
}
```

### API Integration

**API Client (`lib/apiClient.ts`)**
```typescript
// Axios instance with auth interceptor
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Auto-attach auth token
apiClient.interceptors.request.use((config) => {
  const token = getGlobalAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

### Custom Hooks

**useMemoriesApi**
- `fetchMemories()`: Get paginated memories
- `createMemory()`: Add new memory
- `updateMemory()`: Edit memory
- `deleteMemories()`: Bulk delete
- `searchMemories()`: Search with filters

**useAppsApi**
- `fetchApps()`: Get connected apps
- `syncApp()`: Trigger app sync
- `checkTaskStatus()`: Monitor sync progress
- `disconnectApp()`: Remove app connection

## UI Components

### Component Library (shadcn/ui)

**Base Components:**
- Button, Input, Select, Checkbox
- Dialog, Sheet, Drawer
- Table, Card, Badge
- Toast, Alert, Tooltip
- Form controls with validation

**Custom Components:**
- `ParticleBackground`: Animated background
- `ThemeToggle`: Dark/light mode switch
- `UserNav`: User menu dropdown
- `Navbar`: Main navigation

### Styling Approach

**Tailwind CSS**
- Utility-first CSS framework
- Custom theme configuration
- Dark mode support
- Responsive design utilities

**CSS Modules**
- Component-specific styles
- Animation definitions
- Complex layouts

## Performance Optimizations

### 1. Code Splitting
- Dynamic imports for heavy components
- Route-based code splitting
- Lazy loading for modals

### 2. Image Optimization
- Next.js Image component
- Automatic format selection
- Responsive image loading

### 3. State Management
- Redux Toolkit for efficient updates
- Memoized selectors
- Normalized data structures

### 4. API Optimization
- Request debouncing
- Pagination for large datasets
- Caching strategies
- Optimistic updates

## Real-time Features

### Supabase Realtime
- Memory updates across sessions
- App sync status updates
- Collaborative features

### WebSocket Integration
```typescript
// Subscribe to memory changes
supabase
  .channel('memories')
  .on('postgres_changes', {
    event: '*',
    schema: 'public',
    table: 'memories',
    filter: `user_id=eq.${userId}`
  }, handleMemoryChange)
  .subscribe()
```

## Security Considerations

### 1. Authentication
- JWT tokens with expiration
- Secure token storage
- HTTPS-only cookies
- CSRF protection

### 2. Data Protection
- Client-side encryption for sensitive data
- API request sanitization
- XSS prevention
- Content Security Policy

### 3. Environment Variables
- Public vs private variables
- Build-time vs runtime config
- Secret management

## Development Workflow

### Local Development
```bash
# Install dependencies
pnpm install

# Run development server
pnpm dev

# Build for production
pnpm build

# Run production build
pnpm start
```

### Environment Setup
```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_POSTHOG_KEY=your-posthog-key
```

## Testing Strategy

### Unit Tests
- Component testing with React Testing Library
- Hook testing with renderHook
- Redux slice testing

### Integration Tests
- API integration tests
- Auth flow testing
- Form submission tests

### E2E Tests
- Critical user journeys
- Cross-browser testing
- Mobile responsiveness

## Deployment

### Build Process
1. TypeScript compilation
2. Next.js optimization
3. Asset minification
4. Image optimization
5. Static generation where possible

### Production Considerations
- Environment variable validation
- Error boundary implementation
- Performance monitoring
- Analytics integration
- SEO optimization