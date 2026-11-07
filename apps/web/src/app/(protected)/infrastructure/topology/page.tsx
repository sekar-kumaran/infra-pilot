"use client";

import useSWR from 'swr';
import { fetchApi } from '@/lib/api/client';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Network, Server, Database, Globe, Maximize, ZoomIn, ZoomOut, AlertTriangle, RefreshCw, Box } from "lucide-react";
import { useState } from "react";

interface TopologyNode {
  id: string;
  label: string;
  type: string;
  provider: string;
}

export default function TopologyPage() {
  const [selectedNode, setSelectedNode] = useState<TopologyNode | null>(null);

  const { data: topology, error, isLoading, mutate } = useSWR(
    '/infrastructure/topology',
    () => fetchApi<{ nodes: TopologyNode[]; edges: any[] }>('/infrastructure/topology'),
    { refreshInterval: 30000 }
  );

  const getIcon = (type: string) => {
    switch (type) {
      case 'ingress': return Globe;
      case 'lb': return Network;
      case 'db':
      case 'cache': return Database;
      default: return Server;
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case 'ingress': return 'text-sky-400 bg-sky-900/30 border-sky-700';
      case 'lb': return 'text-indigo-400 bg-indigo-900/30 border-indigo-700';
      case 'app': return 'text-emerald-400 bg-emerald-900/30 border-emerald-700';
      case 'db': return 'text-blue-400 bg-blue-900/30 border-blue-700';
      case 'cache': return 'text-orange-400 bg-orange-900/30 border-orange-700';
      default: return 'text-slate-400 bg-slate-800/50 border-slate-700';
    }
  };

  const getProviderBadge = (provider: string) => {
    if (!provider) return null;
    const colors: Record<string, string> = {
      aws: 'bg-orange-900/30 text-orange-400 border-orange-800',
      gcp: 'bg-blue-900/30 text-blue-400 border-blue-800',
      azure: 'bg-sky-900/30 text-sky-400 border-sky-800',
      kubernetes: 'bg-indigo-900/30 text-indigo-400 border-indigo-800',
    };
    return colors[provider.toLowerCase()] || 'bg-slate-800 text-slate-400 border-slate-700';
  };

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Topology Map</h1>
          <p className="text-muted-foreground mt-1">
            Infrastructure graph auto-discovered from your providers.
            {topology?.nodes?.length ? ` ${topology.nodes.length} nodes found.` : ''}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => mutate()}>
            <RefreshCw className="w-4 h-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      <div className="flex-1 flex gap-6 overflow-hidden">
        {/* Graph Canvas */}
        <Card className="flex-1 overflow-auto shadow-sm relative bg-[#0f172a] border-slate-800">
          <div
            className="absolute inset-0"
            style={{ backgroundImage: 'radial-gradient(#1e293b 1px, transparent 1px)', backgroundSize: '32px 32px' }}
          />

          <div className="relative z-10 p-6 min-h-full">
            {isLoading ? (
              <div className="flex items-center justify-center h-64 text-slate-400 gap-2">
                <RefreshCw className="w-5 h-5 animate-spin" /> Discovering infrastructure topology...
              </div>
            ) : error ? (
              <div className="p-8 max-w-lg mx-auto mt-8">
                <div className="bg-rose-950/50 border border-rose-900 text-rose-400 p-4 rounded-md">
                  <h3 className="font-bold flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" /> Topology Map Unavailable
                  </h3>
                  <p className="font-mono text-sm mt-2">API: /api/v1/infrastructure/topology</p>
                  <p className="text-sm mt-1">Reason: {error.message}</p>
                </div>
              </div>
            ) : !topology?.nodes?.length ? (
              <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                <Globe className="w-12 h-12 mb-4 opacity-50" />
                <p className="text-lg font-medium">No infrastructure nodes discovered</p>
                <p className="text-sm mt-2 text-slate-500">Connect a provider integration to begin mapping your architecture.</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {topology.nodes.map((node) => {
                  const Icon = getIcon(node.type);
                  const colorClass = getColor(node.type);
                  const isSelected = selectedNode?.id === node.id;
                  return (
                    <button
                      key={node.id}
                      onClick={() => setSelectedNode(isSelected ? null : node)}
                      className={`
                        flex flex-col items-center gap-2 p-4 rounded-xl border transition-all text-center
                        ${colorClass}
                        ${isSelected ? 'ring-2 ring-indigo-500 scale-105' : 'hover:scale-105'}
                      `}
                    >
                      <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-black/20">
                        <Icon className="w-5 h-5" />
                      </div>
                      <span className="text-xs font-medium truncate w-full">{node.label}</span>
                      <span className="text-[10px] uppercase tracking-wider opacity-60">{node.type}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </Card>

        {/* Node Detail Panel */}
        {selectedNode && (
          <Card className="w-72 shrink-0 bg-slate-900 border-slate-800 overflow-auto">
            <CardHeader className="border-b border-slate-800 pb-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-3 border ${getColor(selectedNode.type)}`}>
                {(() => {
                  const Icon = getIcon(selectedNode.type);
                  return <Icon className="w-6 h-6" />;
                })()}
              </div>
              <CardTitle className="text-slate-100 text-lg">{selectedNode.label}</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Resource Type</p>
                <Badge variant="outline" className="text-slate-300 border-slate-700 capitalize">{selectedNode.type}</Badge>
              </div>
              {selectedNode.provider && (
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Provider</p>
                  <Badge
                    variant="outline"
                    className={`capitalize ${getProviderBadge(selectedNode.provider)}`}
                  >
                    {selectedNode.provider}
                  </Badge>
                </div>
              )}
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Resource ID</p>
                <p className="font-mono text-xs text-slate-400 break-all">{selectedNode.id}</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
