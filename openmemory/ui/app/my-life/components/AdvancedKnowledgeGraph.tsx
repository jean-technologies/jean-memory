"use client";

import React, { useRef, useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { 
  Search, 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  Filter,
  Layers,
  Clock,
  Network,
  Brain,
  User,
  MapPin,
  Calendar,
  Hash,
  Package,
  Heart,
  Sparkles,
  RefreshCw,
  X,
  ChevronRight,
  Info
} from "lucide-react";
import apiClient from "@/lib/apiClient";
import { useSelector } from "react-redux";
import { RootState } from "@/store/store";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

// Dynamic imports for client-side only
let cytoscape: any;
let cola: any;
let fcose: any;

// Initialize Cytoscape and extensions only on client-side
const initializeCytoscape = async () => {
  if (typeof window !== 'undefined' && !cytoscape) {
    cytoscape = (await import('cytoscape')).default;
    cola = (await import('cytoscape-cola')).default;
    fcose = (await import('cytoscape-fcose')).default;
    
    // Register layout extensions
    cytoscape.use(cola);
    cytoscape.use(fcose);
  }
  return cytoscape;
};

interface Memory {
  id: string;
  content: string;
  created_at: string;
  metadata?: any;
  source?: string;
}

interface Entity {
  id: string;
  type: 'Person' | 'Place' | 'Event' | 'Topic' | 'Object' | 'Emotion';
  name: string;
  attributes?: Record<string, any>;
}

interface GraphNode {
  id: string;
  type: 'memory' | 'entity' | 'cluster' | 'temporal';
  label: string;
  data: Memory | Entity | any;
  position?: { x: number; y: number };
  cluster?: string;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  weight?: number;
}

interface ViewMode {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  layoutConfig: any;
}

const VIEW_MODES: ViewMode[] = [
  {
    id: 'overview',
    name: 'Overview',
    icon: Network,
    description: 'High-level view of your knowledge graph',
    layoutConfig: {
      name: 'fcose',
      quality: 'proof',
      randomize: false,
      animate: true,
      animationDuration: 1000,
      nodeRepulsion: 6000,
      idealEdgeLength: 80,
      edgeElasticity: 0.45,
      nestingFactor: 0.1,
      gravity: 0.25,
      numIter: 2500,
      tile: true,
      tilingPaddingVertical: 10,
      tilingPaddingHorizontal: 10,
    }
  },
  {
    id: 'temporal',
    name: 'Timeline',
    icon: Clock,
    description: 'Chronological view of memories and events',
    layoutConfig: {
      name: 'preset',
      positions: (node: any) => {
        // Simple timeline: all nodes on a horizontal line positioned by date
        const createdAt = node.data('created_at');
        if (!createdAt) {
          return { x: 100, y: 300 };
        }
        
        const nodeDate = new Date(createdAt);
        const now = new Date();
        const oneYearAgo = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
        
        // Simple timeline calculation
        const totalTimeSpan = now.getTime() - oneYearAgo.getTime();
        const nodeTimeFromStart = Math.max(0, nodeDate.getTime() - oneYearAgo.getTime());
        const timelineProgress = nodeTimeFromStart / totalTimeSpan;
        
        // Timeline positioning: all on same horizontal line
        const xPosition = 50 + (timelineProgress * 900); // 900px timeline width
        const yPosition = 300 + (Math.random() - 0.5) * 60; // Small vertical jitter to prevent exact overlap
        
        return { x: xPosition, y: yPosition };
      },
      animate: true,
      animationDuration: 800,
      fit: true,
      padding: 60
    }
  },
  {
    id: 'semantic',
    name: 'By Source',
    icon: Layers,
    description: 'Memories organized by source app in concentric rings',
    layoutConfig: {
      name: 'concentric',
      animate: true,
      animationDuration: 1000,
      fit: true,
      padding: 30,
      startAngle: 0,
      sweep: Math.PI * 2,
      clockwise: true,
      equidistant: false,
      minNodeSpacing: 60,
      boundingBox: undefined,
      avoidOverlap: true,
      height: undefined,
      width: undefined,
      spacingFactor: undefined,
      concentric: (node: any) => {
        const nodeType = node.data('nodeType');
        const source = node.data('source')?.toLowerCase() || '';
        const importance = node.data('importance') || 1;
        
        // Create semantic rings: source apps in outer rings, general memories in inner rings
        if (source === 'claude' || source === 'cursor') return 4; // Outermost ring for development tools
        if (source === 'twitter' || source === 'windsurf') return 3; // Social/creative tools
        if (source === 'chatgpt' || source === 'jean memory') return 2; // AI tools
        if (nodeType === 'entity') return 1; // Entities in center
        return Math.max(1, 5 - importance); // Other memories by importance
      },
      levelWidth: (nodes: any) => {
        // Wider rings for more nodes
        return Math.max(2, Math.ceil(nodes.length / 6));
      }
    }
  },
  {
    id: 'entities',
    name: 'Entities',
    icon: Layers,
    description: 'Focus on people, places, and things',
    layoutConfig: {
      name: 'concentric',
      animate: true,
      animationDuration: 1000,
      fit: true,
      padding: 40,
      startAngle: 0,
      sweep: Math.PI * 2,
      clockwise: true,
      equidistant: false,
      minNodeSpacing: 40,
      levelWidth: () => 3,
      concentric: (node: any) => {
        const nodeType = node.data('nodeType');
        // Put memories in center, entities in outer ring
        if (nodeType === 'memory') return 2;
        if (nodeType === 'entity') return 1; 
        return 1;
      }
    }
  }
];

const ENTITY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'person': User,
  'place': MapPin,
  'event': Calendar,
  'topic': Hash,
  'object': Package,
  'emotion': Heart,
  'memory': Brain,
  'cluster': Network
};

// Elegant blue gradient color scheme for clean, cohesive look
const BLUE_GRADIENT_COLORS = {
  'primary': '#0EA5E9',     // Sky blue (primary nodes)
  'secondary': '#0284C7',   // Deeper blue (important nodes)
  'accent': '#0369A1',      // Dark blue (clusters)
  'light': '#38BDF8',       // Light blue (secondary)
  'subtle': '#7DD3FC'       // Very light blue (background)
};

const ENTITY_COLORS: Record<string, string> = {
  'person': BLUE_GRADIENT_COLORS.primary,
  'place': BLUE_GRADIENT_COLORS.secondary,
  'event': BLUE_GRADIENT_COLORS.accent,
  'topic': BLUE_GRADIENT_COLORS.light,
  'object': BLUE_GRADIENT_COLORS.primary,
  'emotion': BLUE_GRADIENT_COLORS.subtle,
  'memory': BLUE_GRADIENT_COLORS.primary,
  'cluster': BLUE_GRADIENT_COLORS.accent
};

interface AdvancedKnowledgeGraphProps {
  onMemorySelect?: (memoryId: string) => void;
}

function AdvancedKnowledgeGraphInner({ onMemorySelect }: AdvancedKnowledgeGraphProps) {
  const cyRef = useRef<HTMLDivElement>(null);
  const cyInstance = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>(VIEW_MODES[0]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [graphStats, setGraphStats] = useState({
    nodes: 0,
    edges: 0,
    entities: 0,
    memories: 0
  });
  const [zoomLevel, setZoomLevel] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [isExpanding, setIsExpanding] = useState(false);
  
  const userId = useSelector((state: RootState) => state.profile.userId);

  // Jean Memory brand colors and styling functions
  const getBrandColorForNode = (node: any) => {
    // Beautiful Jean Memory color palette with gradients
    const importance = node.strength || 1;
    const nodeType = node.type || 'memory';
    
    // App-specific colors for memories with Jean Memory aesthetic
    if (nodeType === 'memory') {
      const appColors: { [key: string]: string } = {
        'claude': '#8B5CF6',     // Purple
        'cursor': '#F59E0B',     // Amber
        'twitter': '#06B6D4',    // Cyan
        'windsurf': '#EC4899',   // Pink
        'chatgpt': '#10B981',    // Emerald
        'jean memory': '#6366F1', // Indigo
        'default': importance > 2 ? '#6366F1' : '#8B5CF6' // Dynamic based on importance
      };
      return appColors[node.source?.toLowerCase()] || appColors.default;
    }
    
    // Entity colors with visual hierarchy
    if (nodeType === 'cluster') return '#4338CA'; // Deep indigo for clusters
    if (importance > 3) return '#6366F1';  // Important entities in brand indigo
    if (importance > 1.5) return '#8B5CF6'; // Medium importance in purple
    
    return ENTITY_COLORS[node.entity_type] || ENTITY_COLORS[nodeType] || '#A855F7'; // Light purple default
  };

  // Initialize Cytoscape
  useEffect(() => {
    const initGraph = async () => {
      if (!cyRef.current || isInitialized) return;
      
      try {
        const cytoscapeLib = await initializeCytoscape();
        if (!cytoscapeLib) return;

        cyInstance.current = cytoscapeLib({
      container: cyRef.current,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (ele: any) => getBrandColorForNode(ele.data()) || '#6366F1',
            'label': 'data(label)', // Keep labels visible for readability
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '10px',
            'color': '#ffffff',
            'text-outline-width': 2,
            'text-outline-color': '#000000',
            'text-wrap': 'none',
            'text-max-width': 'none',
            'width': (ele: any) => {
              const importance = ele.data('importance') || 1;
              const type = ele.data('nodeType');
              let baseSize = type === 'cluster' ? 50 : (type === 'entity' ? 40 : 35); // Larger, readable sizes
              return Math.min(baseSize + (importance - 1) * 5, baseSize * 1.3);
            },
            'height': (ele: any) => {
              const importance = ele.data('importance') || 1;
              const type = ele.data('nodeType');
              let baseSize = type === 'cluster' ? 50 : (type === 'entity' ? 40 : 35); // Larger, readable sizes
              return Math.min(baseSize + (importance - 1) * 5, baseSize * 1.3);
            },
            'box-shadow': '0 0 20px rgba(99, 102, 241, 0.4)', // Subtle Jean Memory glow
            'border-width': 1,
            'border-color': 'rgba(255, 255, 255, 0.2)',
            'border-opacity': 0.8,
            'transition-property': 'box-shadow, width, height',
            'transition-duration': '0.3s',
            'overlay-padding': 4,
            'z-index': 10
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 3,
            'border-color': '#ffffff',
            'background-color': (ele: any) => getBrandColorForNode(ele.data()) || '#6366F1',
            'box-shadow': '0 0 20px rgba(99, 102, 241, 0.8)', // Beautiful glow on selection
            'font-size': '11px', // Slightly larger text when selected
            'z-index': 999
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 1, // Consistent thin lines for elegance
            'line-color': 'rgba(156, 163, 175, 0.4)', // Subtle gray with transparency
            'target-arrow-color': 'rgba(156, 163, 175, 0.4)',
            'target-arrow-shape': 'triangle',
            'target-arrow-size': 6,
            'curve-style': 'haystack', // Cleaner straight lines
            'haystack-radius': 0,
            'opacity': 0.4,
            'z-index': 1
          }
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#3B82F6',
            'target-arrow-color': '#3B82F6',
            'opacity': 1,
            'width': 3,
            'z-index': 999
          }
        },
        {
          selector: '.highlighted',
          style: {
            'background-color': '#FBBF24',
            'line-color': '#FBBF24',
            'target-arrow-color': '#FBBF24',
            'transition-property': 'background-color, line-color, target-arrow-color',
            'transition-duration': '0.3s'
          }
        },
        {
          selector: '.faded',
          style: {
            'opacity': 0.25,
            'z-index': 1
          }
        }
      ],
      layout: viewMode.layoutConfig,
      minZoom: 0.1,
      maxZoom: 3,
      wheelSensitivity: 0.2
    });

    // Event handlers
    cyInstance.current.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeData = node.data();
      setSelectedNode(nodeData);
      
      // Highlight connected nodes
      cyInstance.current?.elements().removeClass('highlighted faded');
      node.addClass('highlighted');
      node.neighborhood().addClass('highlighted');
      cyInstance.current?.elements().not(node.neighborhood().union(node)).addClass('faded');
      
      if (nodeData.nodeType === 'memory' && onMemorySelect) {
        onMemorySelect(nodeData.id);
      }
      
      // Expand node if not already expanded and not an expansion node
      if (!expandedNodes.has(nodeData.id) && !nodeData.isExpansion) {
        expandNode(nodeData.id);
      }
    });

    cyInstance.current.on('tap', (evt) => {
      if (evt.target === cyInstance.current) {
        cyInstance.current?.elements().removeClass('highlighted faded');
        setSelectedNode(null);
      }
    });

        cyInstance.current.on('zoom', () => {
          setZoomLevel(cyInstance.current?.zoom() || 1);
        });

        setIsInitialized(true);
        setError(null);
      } catch (err) {
        console.error('Failed to initialize Cytoscape:', err);
        setError('Failed to initialize graph visualization');
      }
    };

    initGraph();

    return () => {
      if (cyInstance.current) {
        cyInstance.current.destroy();
        cyInstance.current = null;
      }
    };
  }, [onMemorySelect]);

  // Fetch and process graph data
  const loadGraphData = useCallback(async () => {
    if (!userId || !isInitialized || !cyInstance.current) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.get('/api/v1/memories/life-graph-data', {
        params: {
          limit: 25,  // Reduced for better performance: 25 core nodes
          include_entities: true,  // Always include entities for proper connections
          include_temporal_clusters: viewMode.id === 'temporal',
          focus_query: searchQuery || undefined,
          progressive: true  // Enable progressive loading mode
        }
      });

      const { nodes, edges, metadata } = response.data;
      
      // Convert to Cytoscape format
      const cyNodes = nodes.map((node: any) => ({
        data: {
          id: node.id,
          label: node.title || (node.content ? node.content.substring(0, 25) : '') || node.name || 'Memory',
          nodeType: node.type,
          created_at: node.created_at,
          ...node
        },
        position: node.position
      }));

      const cyEdges = edges.map((edge: any, index: number) => ({
        data: {
          id: edge.id || `edge_${index}`,
          source: edge.source,
          target: edge.target,
          edgeType: edge.type,
          weight: edge.weight || 1
        }
      }));

      // Update graph
      cyInstance.current?.elements().remove();
      cyInstance.current?.add([...cyNodes, ...cyEdges]);
      
      // Apply layout with better zoom handling
      const layout = cyInstance.current?.layout({
        ...viewMode.layoutConfig,
        stop: () => {
          setTimeout(() => {
            if (viewMode.id === 'semantic') {
              // For semantic concentric view, fit and zoom to show all rings clearly
              cyInstance.current?.fit();
              const currentZoom = cyInstance.current?.zoom() || 1;
              if (currentZoom < 0.6) {
                cyInstance.current?.zoom(0.6); // Slightly higher zoom for concentric rings
              }
            } else {
              // For other views, center with reasonable zoom
              cyInstance.current?.center();
              cyInstance.current?.zoom(0.8);
            }
          }, 100);
        }
      });
      layout?.run();
      
      // Update stats
      setGraphStats({
        nodes: nodes.length,
        edges: edges.length,
        entities: nodes.filter((n: any) => n.type !== 'memory').length,
        memories: nodes.filter((n: any) => n.type === 'memory').length
      });

    } catch (error) {
      console.error('Failed to load graph data:', error);
      setError('Failed to load graph data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [userId, viewMode, searchQuery, isInitialized]);

  // Node expansion function
  const expandNode = useCallback(async (nodeId: string) => {
    if (!userId || expandedNodes.has(nodeId) || isExpanding) {
      return;
    }

    setIsExpanding(true);
    try {
      const response = await apiClient.get(`/api/v1/memories/life-graph-expand/${nodeId}`, {
        params: { limit: 8 }  // Reduced expansion size for better performance
      });

      const { expansion_nodes, expansion_edges } = response.data;
      
      if (expansion_nodes && expansion_edges) {
        // Get the parent node position for smart positioning
        const parentNode = cyInstance.current?.getElementById(nodeId);
        const parentPos = parentNode?.position() || { x: 0, y: 0 };
        
        // Convert expansion nodes to Cytoscape format with circular positioning
        const cyExpansionNodes = expansion_nodes.map((node: any, index: number) => {
          // Position new nodes in a circle around the parent
          const angle = (index / expansion_nodes.length) * 2 * Math.PI;
          const radius = 120; // Closer distance for better readability
          const x = parentPos.x + Math.cos(angle) * radius;
          const y = parentPos.y + Math.sin(angle) * radius;
          
          return {
            data: {
              id: node.id,
              label: node.content ? node.content.substring(0, 20) : (node.name || 'Expanded'),
              content: node.content,
              nodeType: node.type,
              source: node.source,
              isExpansion: true,
              parentNode: nodeId
            },
            position: { x, y }, // Set explicit position around parent
            classes: 'expansion-node'
          };
        });

        const cyExpansionEdges = expansion_edges.map((edge: any) => ({
          data: {
            id: `${edge.source}-${edge.target}`,
            source: edge.source,
            target: edge.target,
            edgeType: edge.type,
            strength: edge.strength
          },
          classes: 'expansion-edge'
        }));

        // Add expansion nodes and edges to graph
        cyInstance.current?.add([...cyExpansionNodes, ...cyExpansionEdges]);
        
        // Re-apply layout to incorporate new nodes
        cyInstance.current?.layout(viewMode.layoutConfig).run();
        
        // Mark node as expanded
        setExpandedNodes(prev => new Set(prev).add(nodeId));
      }
    } catch (error) {
      console.error('Failed to expand node:', error);
    } finally {
      setIsExpanding(false);
    }
  }, [userId, expandedNodes, isExpanding, viewMode]);

  useEffect(() => {
    loadGraphData();
  }, [loadGraphData]);

  // Search functionality
  const handleSearch = useCallback(() => {
    if (!searchQuery) {
      cyInstance.current?.elements().removeClass('highlighted faded');
      return;
    }

    const matches = cyInstance.current?.nodes().filter((node) => {
      const label = node.data('label').toLowerCase();
      const content = node.data('content')?.toLowerCase() || '';
      return label.includes(searchQuery.toLowerCase()) || 
             content.includes(searchQuery.toLowerCase());
    });

    cyInstance.current?.elements().addClass('faded');
    matches?.removeClass('faded').addClass('highlighted');
    matches?.neighborhood().removeClass('faded');
  }, [searchQuery]);

  // Filter by entity type
  const handleFilter = useCallback((type: string) => {
    setFilterType(type);
    
    if (type === 'all') {
      cyInstance.current?.elements().removeClass('faded');
    } else {
      cyInstance.current?.elements().addClass('faded');
      cyInstance.current?.nodes(`[nodeType = "${type}"]`).removeClass('faded');
      cyInstance.current?.nodes(`[nodeType = "${type}"]`).neighborhood().removeClass('faded');
    }
  }, []);

  // Zoom controls
  const handleZoom = useCallback((delta: number) => {
    const newZoom = Math.max(0.1, Math.min(3, zoomLevel + delta));
    cyInstance.current?.zoom(newZoom);
    cyInstance.current?.center();
  }, [zoomLevel]);

  const handleFit = useCallback(() => {
    cyInstance.current?.fit();
  }, []);

  // Get timeline memories for plotting
  const getTimelineMemories = () => {
    if (!cyInstance.current) return [];
    
    const memories = cyInstance.current.nodes().filter(node => node.data('nodeType') === 'memory');
    return memories.map(node => ({
      id: node.data('id'),
      label: node.data('label'),
      content: node.data('content'),
      created_at: node.data('created_at'),
      source: node.data('source')
    }));
  };

  // Calculate position on timeline based on date
  const getTimelinePosition = (createdAt: string) => {
    const now = new Date();
    const oneYearAgo = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
    const memoryDate = new Date(createdAt);
    
    const totalTimeSpan = now.getTime() - oneYearAgo.getTime();
    const memoryTimeFromStart = Math.max(0, memoryDate.getTime() - oneYearAgo.getTime());
    const timelineProgress = Math.min(1, memoryTimeFromStart / totalTimeSpan);
    
    return timelineProgress * 100; // Return percentage position
  };

  // Custom timeline view for temporal visualization
  if (viewMode.id === 'temporal') {
    const timelineMemories = getTimelineMemories();
    
    return (
      <div className="relative w-full h-full bg-background">
        {/* Loading State */}
        <AnimatePresence>
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
            >
              <Card className="p-6">
                <div className="flex flex-col items-center gap-3">
                  <RefreshCw className="w-8 h-8 animate-spin text-primary" />
                  <p className="text-sm text-muted-foreground">Loading timeline...</p>
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Timeline Container */}
        <div className="w-full h-full flex flex-col items-center justify-center p-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-foreground mb-2">Memory Timeline</h2>
            <p className="text-muted-foreground">Chronological view of your memories</p>
            <p className="text-xs text-muted-foreground mt-1">Note: Only showing memories with dates (from July 2024 onwards)</p>
          </div>
          
          {/* Timeline Visualization */}
          <div className="relative w-full max-w-6xl h-80">
            {/* Main timeline axis */}
            <div className="absolute bottom-16 left-0 w-full h-0.5 bg-gradient-to-r from-blue-500/20 via-blue-500/60 to-blue-500/20"></div>
            
            {/* Month markers */}
            {Array.from({ length: 12 }, (_, i) => {
              const monthDate = new Date();
              monthDate.setMonth(monthDate.getMonth() - (11 - i));
              const monthName = monthDate.toLocaleDateString('en', { month: 'short' });
              const position = (i / 11) * 100;
              
              return (
                <div key={i} className="absolute bottom-16" style={{ left: `${position}%` }}>
                  <div className="w-px h-6 bg-border -translate-x-0.5"></div>
                  <div className="text-xs text-muted-foreground mt-2 -translate-x-1/2 whitespace-nowrap">
                    {monthName}
                  </div>
                </div>
              );
            })}
            
            {/* Memory plot points */}
            {timelineMemories.map((memory, index) => {
              if (!memory.created_at) return null;
              
              const position = getTimelinePosition(memory.created_at);
              const verticalOffset = (index % 5) * 40 + 20; // Stack memories vertically to avoid overlap
              const memoryDate = new Date(memory.created_at);
              
              // Color based on source app
              const getMemoryColor = () => {
                const source = memory.source?.toLowerCase() || 'default';
                const colors: { [key: string]: string } = {
                  'claude': '#8B5CF6',
                  'cursor': '#F59E0B', 
                  'twitter': '#06B6D4',
                  'windsurf': '#EC4899',
                  'chatgpt': '#10B981',
                  'jean memory': '#6366F1',
                  'default': '#6366F1'
                };
                return colors[source] || colors.default;
              };
              
              return (
                <motion.div
                  key={memory.id}
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.05 }}
                  className="absolute cursor-pointer group"
                  style={{ 
                    left: `${position}%`,
                    bottom: `${80 + verticalOffset}px`,
                    transform: 'translateX(-50%)'
                  }}
                  onClick={() => {
                    setSelectedNode({
                      ...memory,
                      nodeType: 'memory',
                      label: memory.label || memory.content?.substring(0, 30) + '...'
                    });
                  }}
                >
                  {/* Memory dot */}
                  <div
                    className="w-4 h-4 rounded-full border-2 border-white shadow-lg transition-all duration-200 group-hover:scale-125 group-hover:shadow-xl"
                    style={{ backgroundColor: getMemoryColor() }}
                  />
                  
                  {/* Connection line to timeline */}
                  <div 
                    className="absolute w-px bg-gray-300 opacity-30 group-hover:opacity-60 transition-opacity"
                    style={{
                      left: '50%',
                      top: '16px',
                      height: `${verticalOffset + 16}px`,
                      transform: 'translateX(-50%)'
                    }}
                  />
                  
                  {/* Hover tooltip */}
                  <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-card/95 backdrop-blur-sm rounded-lg p-3 shadow-xl border opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 min-w-64 max-w-80">
                    <div className="text-sm font-medium mb-1">{memory.label || 'Memory'}</div>
                    <div className="text-xs text-muted-foreground mb-2">
                      {memoryDate.toLocaleDateString('en', { 
                        month: 'short', 
                        day: 'numeric',
                        year: 'numeric'
                      })}
                      {memory.source && ` • ${memory.source}`}
                    </div>
                    {memory.content && (
                      <div className="text-xs text-muted-foreground">
                        {memory.content.length > 100 
                          ? memory.content.substring(0, 100) + '...'
                          : memory.content
                        }
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
            
            {/* Timeline labels */}
            <div className="absolute bottom-8 left-0 text-xs text-muted-foreground">
              1 Year Ago
            </div>
            <div className="absolute bottom-8 right-0 text-xs text-muted-foreground">
              Today
            </div>
          </div>
          
          <div className="mt-8 text-sm text-muted-foreground text-center">
            Showing {timelineMemories.length} memories over the past year
          </div>
        </div>

        {/* Control Panel */}
        <div className="absolute top-4 left-4 z-40">
          <Card className="bg-card/90 backdrop-blur-sm p-4">
            <div className="flex gap-2">
              {VIEW_MODES.map((mode) => {
                const Icon = mode.icon;
                return (
                  <Button
                    key={mode.id}
                    variant={viewMode.id === mode.id ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode(mode)}
                  >
                    <Icon className="w-4 h-4 mr-1" />
                    {mode.name}
                  </Button>
                );
              })}
            </div>
          </Card>
        </div>

        {/* Selected Memory Details */}
        <AnimatePresence>
          {selectedNode && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="absolute bottom-4 left-4 right-4 z-40 max-w-2xl mx-auto"
            >
              <Card className="bg-card/95 backdrop-blur-sm">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div 
                        className="p-2 rounded-full"
                        style={{ backgroundColor: '#6366F1' }}
                      >
                        <Brain className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{selectedNode.label}</CardTitle>
                        <CardDescription>
                          {selectedNode.created_at ? 
                            new Date(selectedNode.created_at).toLocaleDateString('en', {
                              weekday: 'long',
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric'
                            }) : 
                            'No date'
                          }
                          {selectedNode.source && ` • ${selectedNode.source}`}
                        </CardDescription>
                      </div>
                    </div>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => setSelectedNode(null)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {selectedNode.content && (
                    <p className="text-sm text-muted-foreground mb-3">
                      {selectedNode.content}
                    </p>
                  )}
                  <Button 
                    size="sm" 
                    className="mt-3"
                    onClick={() => {
                      window.location.href = `/memory/${selectedNode.id}`;
                    }}
                  >
                    View Memory Details
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full bg-background">
      {/* Loading State */}
      <AnimatePresence>
        {(isLoading || isExpanding) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
          >
            <Card className="p-6">
              <div className="flex flex-col items-center gap-3">
                <RefreshCw className="w-8 h-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">
                  {isExpanding ? 'Expanding node connections...' : 'Loading your knowledge graph...'}
                </p>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error State */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
          >
            <Card className="p-6 max-w-md">
              <div className="flex flex-col items-center gap-3">
                <X className="w-8 h-8 text-destructive" />
                <p className="text-sm text-destructive text-center">{error}</p>
                <Button onClick={() => {
                  setError(null);
                  loadGraphData();
                }} size="sm">
                  Try Again
                </Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Control Panel */}
      <div className="absolute top-4 left-4 z-40 flex flex-col gap-4 max-w-sm">
        {/* View Mode Selector */}
        <Card className="bg-card/90 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">View Mode</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-2">
            {VIEW_MODES.map((mode) => {
              const Icon = mode.icon;
              return (
                <Button
                  key={mode.id}
                  variant={viewMode.id === mode.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode(mode)}
                  className="justify-start"
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {mode.name}
                </Button>
              );
            })}
          </CardContent>
        </Card>

        {/* Search */}
        <Card className="bg-card/90 backdrop-blur-sm">
          <CardContent className="pt-4">
            <div className="flex gap-2">
              <Input
                placeholder="Search memories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1"
              />
              <Button size="icon" onClick={handleSearch}>
                <Search className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Entity Filter */}
        <Card className="bg-card/90 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Filter by Type</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Badge 
              variant={filterType === 'all' ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => handleFilter('all')}
            >
              All
            </Badge>
            {Object.entries(ENTITY_ICONS).map(([type, Icon]) => (
              <Badge
                key={type}
                variant={filterType === type ? 'default' : 'outline'}
                className="cursor-pointer flex items-center gap-1"
                onClick={() => handleFilter(type)}
              >
                <Icon className="w-3 h-3" />
                {type}
              </Badge>
            ))}
          </CardContent>
        </Card>

        {/* Graph Stats */}
        <Card className="bg-card/90 backdrop-blur-sm">
          <CardContent className="pt-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Nodes:</span>
              <span className="font-medium">{graphStats.nodes}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Memories:</span>
              <span className="font-medium">{graphStats.memories}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Entities:</span>
              <span className="font-medium">{graphStats.entities}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Connections:</span>
              <span className="font-medium">{graphStats.edges}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Zoom Controls */}
      <div className="absolute top-4 right-4 z-40 flex flex-col gap-2">
        <Button size="icon" variant="outline" onClick={() => handleZoom(0.2)}>
          <ZoomIn className="w-4 h-4" />
        </Button>
        <Button size="icon" variant="outline" onClick={() => handleZoom(-0.2)}>
          <ZoomOut className="w-4 h-4" />
        </Button>
        <Button size="icon" variant="outline" onClick={handleFit}>
          <Maximize2 className="w-4 h-4" />
        </Button>
        <Button size="icon" variant="outline" onClick={loadGraphData}>
          <RefreshCw className="w-4 h-4" />
        </Button>
      </div>

      {/* Selected Node Details */}
      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-4 left-4 right-4 z-40 max-w-2xl mx-auto"
          >
            <Card className="bg-card/95 backdrop-blur-sm">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    {selectedNode.nodeType && ENTITY_ICONS[selectedNode.nodeType] && (
                      <div 
                        className="p-2 rounded-full"
                        style={{ backgroundColor: ENTITY_COLORS[selectedNode.nodeType] }}
                      >
                        {React.createElement(ENTITY_ICONS[selectedNode.nodeType], { 
                          className: "w-4 h-4 text-white" 
                        })}
                      </div>
                    )}
                    <div>
                      <CardTitle className="text-lg">{selectedNode.label}</CardTitle>
                      <CardDescription>
                        {selectedNode.nodeType} • {selectedNode.created_at ? 
                          new Date(selectedNode.created_at).toLocaleDateString() : 
                          'No date'
                        }
                      </CardDescription>
                    </div>
                  </div>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => setSelectedNode(null)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {selectedNode.content && (
                  <p className="text-sm text-muted-foreground mb-3">
                    {selectedNode.content}
                  </p>
                )}
                {selectedNode.attributes && (
                  <div className="space-y-1 text-sm">
                    {Object.entries(selectedNode.attributes).map(([key, value]) => (
                      <div key={key} className="flex gap-2">
                        <span className="text-muted-foreground capitalize">{key}:</span>
                        <span>{String(value)}</span>
                      </div>
                    ))}
                  </div>
                )}
                {selectedNode.nodeType === 'memory' && (
                  <Button 
                    size="sm" 
                    className="mt-3"
                    onClick={() => {
                      // Navigate to memory details page
                      window.location.href = `/memory/${selectedNode.id}`;
                    }}
                  >
                    View Memory Details
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Graph Container */}
      <div ref={cyRef} className="w-full h-full" />

      {/* Help Button */}
      <Button
        size="icon"
        variant="outline"
        className="absolute bottom-4 right-4 z-40"
        onClick={() => {
          // TODO: Show help dialog
        }}
      >
        <Info className="w-4 h-4" />
      </Button>
    </div>
  );
}

// Client-side only wrapper to prevent SSR issues
export default function AdvancedKnowledgeGraph(props: AdvancedKnowledgeGraphProps) {
  const [isClient, setIsClient] = useState(false);
  
  useEffect(() => {
    setIsClient(true);
  }, []);
  
  if (!isClient) {
    return (
      <div className="relative w-full h-full bg-background flex items-center justify-center">
        <Card className="p-6">
          <div className="flex flex-col items-center gap-3">
            <RefreshCw className="w-8 h-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Initializing graph...</p>
          </div>
        </Card>
      </div>
    );
  }
  
  return <AdvancedKnowledgeGraphInner {...props} />;
}