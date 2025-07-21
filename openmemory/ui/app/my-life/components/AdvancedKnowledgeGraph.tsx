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
  Info,
  Target
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
      name: 'cose',
      animate: true,
      animationDuration: 1000,
      nodeRepulsion: 10000,
      nodeOverlap: 20,
      idealEdgeLength: 120,
      edgeElasticity: 100,
      nestingFactor: 0.5,
      gravity: 80,
      numIter: 1000,
      initialTemp: 200,
      coolingFactor: 0.95,
      minTemp: 1.0,
      fit: true,
      padding: 30,
      randomize: false
    }
  },
  {
    id: 'temporal',
    name: 'Timeline',
    icon: Clock,
    description: 'Chronological view of memories and events',
    layoutConfig: {
      name: 'dagre',
      rankDir: 'LR', // Left to right for timeline
      align: 'UL',
      rankSep: 150,
      nodeSep: 100,
      edgeSep: 20,
      marginX: 20,
      marginY: 20,
      animate: true,
      animationDuration: 1000,
      fit: true,
      padding: 50
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
      refresh: 1,
      maxSimulationTime: 4000,
      ungrabifyWhileSimulating: false,
      fit: true,
      padding: 60,
      nodeSpacing: 80,
      edgeLength: 150,
      edgeSymDiffLength: 100,
      edgeJaccardLength: 100,
      randomize: false,
      avoidOverlap: true,
      handleDisconnected: true,
      convergenceThreshold: 0.01
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
      padding: 50,
      startAngle: 0,
      sweep: Math.PI * 2,
      clockwise: true,
      equidistant: false,
      minNodeSpacing: 60,
      levelWidth: () => 2,
      concentric: (node: any) => {
        const nodeType = node.data('nodeType');
        const entityType = node.data('entity_type');
        
        // Put entities in outer rings based on type
        if (nodeType === 'entity') {
          if (entityType === 'person') return 5;
          if (entityType === 'place') return 4;
          if (entityType === 'event') return 3;
          return 2;
        }
        // Memories in the center
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

const ENTITY_COLORS: Record<string, string> = {
  'person': '#3B82F6',      // Blue
  'place': '#10B981',       // Green
  'event': '#F59E0B',       // Amber
  'topic': '#8B5CF6',       // Purple
  'object': '#EF4444',      // Red
  'emotion': '#EC4899',     // Pink
  'memory': '#6B7280',      // Gray
  'cluster': '#1F2937'      // Dark Gray
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
    // Use Jean Memory's chart colors for different node types
    if (node.type === 'memory') {
      // Use app-specific colors based on source
      const appColors: { [key: string]: string } = {
        'claude': 'hsl(240, 70%, 65%)',
        'cursor': 'hsl(45, 80%, 65%)',
        'twitter': 'hsl(200, 80%, 65%)',
        'windsurf': 'hsl(0, 70%, 65%)',
        'chatgpt': 'hsl(180, 60%, 60%)',
        'jean memory': 'hsl(150, 60%, 60%)',
        'default': 'hsl(222, 47%, 45%)'
      };
      return appColors[node.source?.toLowerCase()] || appColors.default;
    }
    
    // Entity colors using Jean Memory's system
    const entityColors: { [key: string]: string } = {
      'person': '#3B82F6',
      'place': '#10B981', 
      'event': '#F59E0B',
      'topic': '#8B5CF6',
      'object': '#EF4444',
      'emotion': '#EC4899',
      'default': '#6B7280'
    };
    
    return entityColors[node.entity_type] || entityColors.default;
  };

  const getSmartNodeSize = (node: any) => {
    // Progressive sizing based on content and importance
    if (node.type === 'memory') {
      const contentLength = node.content?.length || 0;
      const baseSize = 40;
      const sizeBonus = Math.min(contentLength / 100, 20); // Up to 20px bonus
      return baseSize + sizeBonus;
    }
    return 35; // Smaller for entities
  };

  const getNodeClasses = (node: any) => {
    let classes = 'jean-node';
    if (node.type === 'memory') classes += ' memory-node';
    if (node.is_expansion) classes += ' expansion-node';
    return classes;
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
            'background-color': (ele: any) => ENTITY_COLORS[ele.data('nodeType')] || '#6B7280',
            'label': (ele: any) => {
              const label = ele.data('label') || '';
              const nodeType = ele.data('nodeType');
              
              // Different truncation for different node types
              if (nodeType === 'entity') {
                return label.length > 20 ? label.substring(0, 18) + '...' : label;
              } else if (nodeType === 'cluster') {
                return label.length > 30 ? label.substring(0, 27) + '...' : label;
              } else {
                return label.length > 35 ? label.substring(0, 32) + '...' : label;
              }
            },
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': (ele: any) => {
              const type = ele.data('nodeType');
              if (type === 'cluster') return '14px';
              if (type === 'entity') return '11px';
              return '10px';
            },
            'color': '#ffffff',
            'text-outline-width': 2,
            'text-outline-color': '#000000',
            'font-weight': 'bold',
            'text-wrap': 'wrap',
            'text-max-width': (ele: any) => {
              const type = ele.data('nodeType');
              if (type === 'cluster') return '140px';
              if (type === 'entity') return '100px';
              return '120px';
            },
            'width': (ele: any) => {
              const type = ele.data('nodeType');
              const importance = ele.data('importance') || 1;
              
              let baseSize;
              if (type === 'cluster') baseSize = 80;
              else if (type === 'entity') baseSize = 50;
              else baseSize = 35;
              
              // Scale based on importance but keep reasonable bounds
              return Math.min(Math.max(baseSize + (importance - 1) * 5, baseSize * 0.8), baseSize * 1.5);
            },
            'height': (ele: any) => {
              const type = ele.data('nodeType');
              const importance = ele.data('importance') || 1;
              
              let baseSize;
              if (type === 'cluster') baseSize = 80;
              else if (type === 'entity') baseSize = 50;
              else baseSize = 35;
              
              // Scale based on importance but keep reasonable bounds
              return Math.min(Math.max(baseSize + (importance - 1) * 5, baseSize * 0.8), baseSize * 1.5);
            },
            'overlay-padding': 8,
            'z-index': 10,
            'border-width': 2,
            'border-color': '#ffffff',
            'border-opacity': 0.3
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#ffffff',
            'background-color': (ele: any) => ENTITY_COLORS[ele.data('nodeType')] || '#6B7280',
            'width': (ele: any) => {
              const type = ele.data('nodeType');
              if (type === 'cluster') return 110;
              if (type === 'entity') return 70;
              return 50;
            },
            'height': (ele: any) => {
              const type = ele.data('nodeType');
              if (type === 'cluster') return 110;
              if (type === 'entity') return 70;
              return 50;
            },
            'z-index': 999,
            'box-shadow': '0 0 20px rgba(255, 255, 255, 0.5)'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': (ele: any) => Math.max(2, (ele.data('weight') || 1) * 2),
            'line-color': '#6B7280',
            'target-arrow-color': '#6B7280',
            'target-arrow-shape': 'triangle',
            'target-arrow-size': 8,
            'curve-style': 'haystack',
            'haystack-radius': 0.3,
            'opacity': 0.4,
            'z-index': 1
          }
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#3B82F6',
            'target-arrow-color': '#3B82F6',
            'opacity': 0.8,
            'width': 4,
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
      maxZoom: 5,
      wheelSensitivity: 0.1,
      boxSelectionEnabled: false,
      autounselectify: false,
      autoungrabify: false,
      userZoomingEnabled: true,
      userPanningEnabled: true,
      selectionType: 'single'
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
          limit: viewMode.id === 'overview' ? 25 : 30,  // More meaningful initial load
          include_entities: viewMode.id === 'entities',  // Include entities for entity view
          include_temporal_clusters: viewMode.id === 'temporal',
          focus_query: searchQuery || undefined,
          progressive: true  // Enable progressive loading mode
        }
      });

      const { nodes, edges, metadata } = response.data;
      
      // Convert to Cytoscape format with improved styling and rich labels
      const cyNodes = nodes.map((node: any, index: number) => {
        // Create meaningful labels based on content
        let label = node.title || node.name;
        
        if (!label && node.content) {
          // Extract meaningful content for label - avoid generic starts
          let content = node.content.trim();
          
          // Remove common prefixes
          content = content.replace(/^(User |I |The user |They |This |That |It |A |An )/i, '');
          
          // Take first meaningful sentence or phrase
          const sentences = content.split(/[.!?]/);
          label = sentences[0].substring(0, 35).trim();
          if (content.length > 35) label += '...';
        }
        
        if (!label) label = node.type === 'entity' ? node.entity_type || 'Entity' : 'Memory';
        
        return {
          data: {
            id: node.id,
            label: label,
            nodeType: node.type || 'memory',
            entity_type: node.entity_type,
            created_at: node.created_at,
            source: node.source,
            content: node.content,
            title: node.title,
            name: node.name,
            brandColor: getBrandColorForNode(node),
            size: getSmartNodeSize(node),
            importance: node.strength || 1,
            ...node
          },
          // Don't set position initially - let layout handle it
          classes: getNodeClasses(node)
        };
      });

      const cyEdges = edges.map((edge: any, index: number) => ({
        data: {
          id: edge.id || `edge_${index}`,
          source: edge.source,
          target: edge.target,
          edgeType: edge.type,
          weight: edge.weight || 1
        }
      }));

      // Update graph with better rendering
      cyInstance.current?.elements().remove();
      cyInstance.current?.add([...cyNodes, ...cyEdges]);
      
      // Apply layout with fit and center
      const layout = cyInstance.current?.layout({
        ...viewMode.layoutConfig,
        stop: () => {
          // Center and fit the graph after layout completes
          setTimeout(() => {
            cyInstance.current?.fit(undefined, 50);
            cyInstance.current?.center();
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
        params: { limit: 10 }  // Reasonable expansion size
      });

      const { expansion_nodes, expansion_edges } = response.data;
      
      if (expansion_nodes && expansion_edges) {
        // Get the parent node position for smart positioning
        const parentNode = cyInstance.current?.getElementById(nodeId);
        const parentPos = parentNode?.position() || { x: 0, y: 0 };
        
        // Convert expansion nodes to Cytoscape format with smart positioning
        const cyExpansionNodes = expansion_nodes.map((node: any, index: number) => {
          // Position new nodes in a circle around the parent with better spacing
          const angle = (index / expansion_nodes.length) * 2 * Math.PI;
          const radius = 180; // Good distance from parent node
          const x = parentPos.x + Math.cos(angle) * radius;
          const y = parentPos.y + Math.sin(angle) * radius;
          
          // Create meaningful labels for expansion nodes using same logic as main nodes
          let label = node.title || node.name;
          
          if (!label && node.content) {
            // Extract meaningful content for label - avoid generic starts
            let content = node.content.trim();
            
            // Remove common prefixes
            content = content.replace(/^(User |I |The user |They |This |That |It |A |An )/i, '');
            
            // Take first meaningful sentence or phrase
            const sentences = content.split(/[.!?]/);
            label = sentences[0].substring(0, 30).trim();
            if (content.length > 30) label += '...';
          }
          
          if (!label) label = node.type === 'entity' ? node.entity_type || 'Entity' : 'Expanded Memory';
          
          return {
            data: {
              id: node.id,
              label: label,
              content: node.content,
              nodeType: node.type || 'memory',
              entity_type: node.entity_type,
              source: node.source,
              title: node.title,
              name: node.name,
              isExpansion: true,
              parentNode: nodeId
            },
            position: { x, y }, // Set explicit position
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
        
        // Apply a gentle force-directed adjustment to integrate new nodes
        const layoutConfig = {
          name: 'cose',
          animate: true,
          animationDuration: 800,
          nodeRepulsion: 5000,
          idealEdgeLength: 80,
          edgeElasticity: 32,
          numIter: 100,
          fit: false,
          randomize: false,
          // Only apply to expansion nodes and their immediate neighbors
          boundingBox: {
            x1: parentPos.x - 300,
            y1: parentPos.y - 300,
            x2: parentPos.x + 300,
            y2: parentPos.y + 300
          }
        };
        
        cyInstance.current?.layout(layoutConfig).run();
        
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
    const newZoom = Math.max(0.1, Math.min(5, zoomLevel + delta));
    cyInstance.current?.zoom({
      level: newZoom,
      renderedPosition: { x: cyRef.current!.clientWidth / 2, y: cyRef.current!.clientHeight / 2 }
    });
  }, [zoomLevel]);

  const handleFit = useCallback(() => {
    cyInstance.current?.fit(undefined, 50);
  }, []);
  
  const handleCenter = useCallback(() => {
    cyInstance.current?.center();
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
        <Button size="icon" variant="outline" onClick={handleCenter}>
          <Target className="w-4 h-4" />
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