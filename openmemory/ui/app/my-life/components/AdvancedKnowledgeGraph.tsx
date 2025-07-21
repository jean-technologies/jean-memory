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
      name: 'cose',
      animate: true,
      animationDuration: 1000,
      nodeRepulsion: 4000,
      idealEdgeLength: 50,
      edgeElasticity: 100,
      nestingFactor: 0.1,
      gravity: 80,
      numIter: 1000,
      initialTemp: 200,
      coolingFactor: 0.95,
      minTemp: 1.0,
      fit: true,
      padding: 20,
      randomize: false
    }
  },
  {
    id: 'semantic',
    name: 'Semantic',
    icon: Brain,
    description: 'Memories clustered by meaning and topics',
    layoutConfig: {
      name: 'cola',
      animate: true,
      maxSimulationTime: 4000,
      ungrabifyWhileSimulating: true,
      fit: true,
      padding: 30,
      nodeSpacing: 50,
      edgeLength: 100,
      randomize: false
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
          label: node.title || (node.content ? node.content.substring(0, 15) + '...' : '') || node.name || 'Memory',
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
      
      // Apply layout with reasonable zoom level
      const layout = cyInstance.current?.layout({
        ...viewMode.layoutConfig,
        stop: () => {
          // Center but don't auto-fit to avoid tiny nodes
          setTimeout(() => {
            cyInstance.current?.center();
            // Set a reasonable zoom level instead of auto-fit
            cyInstance.current?.zoom(0.8);
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
              label: node.content ? (node.content.substring(0, 12) + '...') : (node.name || 'Expanded'),
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