"use client";

import useSWR from 'swr';
import { observabilityApi, LiveEvent } from '@/lib/api/observability';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, Rocket, AlertTriangle, CheckCircle, RefreshCw, Server } from "lucide-react";
import { useEffect, useState } from 'react';

export default function LiveFeedPage() {
  const { data: initialEvents, error } = useSWR('/observability/live-events', () => observabilityApi.getLiveEvents(50));
  const [events, setEvents] = useState<LiveEvent[]>([]);

  useEffect(() => {
    if (initialEvents) {
      setEvents(initialEvents);
    }
  }, [initialEvents]);



  const getEventIcon = (type: string) => {
    switch (type) {
      case 'deployment': return <Rocket className="w-5 h-5 text-indigo-500" />;
      case 'alert': return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case 'healthcheck': return <CheckCircle className="w-5 h-5 text-emerald-500" />;
      case 'scaling': return <Activity className="w-5 h-5 text-blue-500" />;
      default: return <Server className="w-5 h-5 text-slate-500" />;
    }
  };

  const getEventBg = (type: string) => {
    switch (type) {
      case 'deployment': return 'bg-indigo-50 dark:bg-indigo-500/10 border-indigo-100 dark:border-indigo-500/20';
      case 'alert': return 'bg-orange-50 dark:bg-orange-500/10 border-orange-100 dark:border-orange-500/20';
      case 'healthcheck': return 'bg-emerald-50 dark:bg-emerald-500/10 border-emerald-100 dark:border-emerald-500/20';
      case 'scaling': return 'bg-blue-50 dark:bg-blue-500/10 border-blue-100 dark:border-blue-500/20';
      default: return 'bg-slate-50 dark:bg-slate-800/50 border-slate-100 dark:border-slate-700/50';
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Live Feed</h1>
          <p className="text-muted-foreground mt-1">Real-time stream of all events and metrics across your infrastructure.</p>
        </div>
        <div className="flex items-center gap-2 text-emerald-500 text-sm font-medium bg-emerald-50 dark:bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-200 dark:border-emerald-500/20">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Live Connection Active
        </div>
      </div>

      <Card className="flex-1 overflow-hidden shadow-sm">
        <CardContent className="p-0 h-[calc(100vh-14rem)] overflow-y-auto">
          {error ? (
            <div className="p-8">
              <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-md">
                <h3 className="font-bold flex items-center gap-2"><AlertTriangle className="w-5 h-5"/> Failed to connect to event stream</h3>
                <p className="font-mono text-sm mt-2">API: /api/v1/observability/live-events</p>
                <p className="text-sm mt-1">Reason: {error.message}</p>
              </div>
            </div>
          ) : events.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin mb-4 text-indigo-400" />
              Initializing live stream...
            </div>
          ) : (
            <div className="divide-y">
              {events.map((event, idx) => (
                <div key={event.id} className={`p-4 flex gap-4 transition-all hover:bg-slate-50/50 dark:hover:bg-slate-800/50 ${idx === 0 ? 'animate-in slide-in-from-top-4 fade-in duration-500' : ''}`}>
                  <div className={`shrink-0 w-12 h-12 rounded-xl flex items-center justify-center border ${getEventBg(event.type)}`}>
                    {getEventIcon(event.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start mb-1">
                      <p className="font-medium text-slate-900 dark:text-slate-100">{event.description}</p>
                      <span className="text-xs text-slate-500 whitespace-nowrap ml-4">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[10px] uppercase font-mono tracking-wider bg-white dark:bg-slate-950">
                        {event.source}
                      </Badge>
                      <span className="text-sm text-slate-500 capitalize">{event.type.replace('_', ' ')}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
