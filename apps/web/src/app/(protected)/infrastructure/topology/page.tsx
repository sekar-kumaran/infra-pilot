"use client";

import useSWR from 'swr';
import { fetchApi } from '@/lib/api/client';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Network, Server, Database, Globe, Maximize, ZoomIn, ZoomOut, AlertTriangle, RefreshCw } from "lucide-react";
import { useState } from "react";

export default function TopologyPage() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const { data: topology, error, isLoading } = useSWR('/infrastructure/topology', () => fetchApi<{ nodes: any[]; edges: any[] }>('/infrastructure/topology'));


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
      case 'ingress': return 'text-sky-500 bg-sky-100 dark:bg-sky-900/30';
      case 'lb': return 'text-indigo-500 bg-indigo-100 dark:bg-indigo-900/30';
      case 'app': return 'text-emerald-500 bg-emerald-100 dark:bg-emerald-900/30';
      case 'db': return 'text-blue-500 bg-blue-100 dark:bg-blue-900/30';
      case 'cache': return 'text-orange-500 bg-orange-100 dark:bg-orange-900/30';
      default: return 'text-slate-500 bg-slate-100 dark:bg-slate-900/30';
    }
  };

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Topology Map</h1>
          <p className="text-muted-foreground mt-1">Interactive infrastructure graph auto-discovered from your providers.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon"><ZoomIn className="w-4 h-4" /></Button>
          <Button variant="outline" size="icon"><ZoomOut className="w-4 h-4" /></Button>
          <Button variant="outline" size="icon"><Maximize className="w-4 h-4" /></Button>
        </div>
      </div>

      <div className="flex-1 flex gap-6 overflow-hidden">
        {/* Graph Canvas */}
        <Card className="flex-1 overflow-hidden shadow-sm relative bg-[#0f172a] border-slate-800">
          <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(#1e293b 1px, transparent 1px)', backgroundSize: '32px 32px' }} />
          
          <div className="absolute inset-0 w-full h-full p-12 flex items-center justify-center">
            {isLoading ? (
              <div className="text-slate-400 flex items-center gap-2 relative z-20"><RefreshCw className="w-5 h-5 animate-spin" /> Discovering infrastructure topology...</div>
            ) : error ? (
              <div className="p-8 relative z-20 max-w-lg w-full">
                <div className="bg-rose-950/50 border border-rose-900 text-rose-400 p-4 rounded-md">
                  <h3 className="font-bold flex items-center gap-2"><AlertTriangle className="w-5 h-5"/> Topology Map Unavailable</h3>
                  <p className="font-mono text-sm mt-2">API: /api/v1/infrastructure/topology</p>
                  <p className="text-sm mt-1">Reason: {error.message}</p>
                </div>
              </div>
            ) : !topology?.nodes?.length ? (
              <div className="text-slate-400 text-center relative z-20">
                <Globe className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No infrastructure nodes discovered.</p>
                <p className="text-sm mt-2">Connect a provider to begin mapping your architecture.</p>
              </div>
            ) : (
              <div className="relative w-full h-full max-w-4xl mx-auto">
                {/* Simulated Graph Renderer if data existed */}
                <div className="text-emerald-400 font-mono">Successfully loaded {topology.nodes.length} nodes. Graph renderer not fully implemented.</div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
