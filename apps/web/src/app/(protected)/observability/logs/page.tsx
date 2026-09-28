"use client";

import { useState } from 'react';
import useSWR from 'swr';
import { observabilityApi } from '@/lib/api/observability';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, Terminal, Download, RefreshCw, AlertCircle } from "lucide-react";
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, YAxis } from 'recharts';

export default function LogsExplorerPage() {
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: logs, error, isLoading, mutate } = useSWR(
    ['/observability/logs', searchQuery, level], 
    () => observabilityApi.getLogs(searchQuery, level === 'all' ? undefined : level)
  );

  const getLevelColor = (lvl: string) => {
    switch (lvl) {
      case 'ERROR': return 'text-red-400';
      case 'WARN': return 'text-yellow-400';
      case 'INFO': return 'text-emerald-400';
      case 'DEBUG': return 'text-slate-400';
      default: return 'text-slate-400';
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(query);
  };

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Logs Explorer</h1>
          <p className="text-muted-foreground mt-1">Search, filter, and analyze centralized logs.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => mutate()}><RefreshCw className="w-4 h-4 mr-2" /> Refresh</Button>
          <Button variant="outline"><Download className="w-4 h-4 mr-2" /> Export</Button>
        </div>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden border-slate-200 dark:border-slate-800 shadow-sm">
        <CardHeader className="bg-slate-50 dark:bg-slate-900/50 border-b pb-4 pt-4">
          <form onSubmit={handleSearch} className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input 
                placeholder="Search logs by keyword, trace_id, or service..." 
                className="pl-10"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <Select value={level} onValueChange={(val) => setLevel(val as string)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Severity Level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="ERROR">Error</SelectItem>
                <SelectItem value="WARN">Warning</SelectItem>
                <SelectItem value="INFO">Info</SelectItem>
                <SelectItem value="DEBUG">Debug</SelectItem>
              </SelectContent>
            </Select>
            <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700">Search</Button>
          </form>
        </CardHeader>
        
        <CardContent className="flex-1 p-0 bg-[#0f172a] overflow-hidden relative">
          <div className="absolute top-4 right-4 text-slate-500/50 flex items-center">
            <Terminal className="w-16 h-16" />
          </div>
          
          <div className="h-full overflow-y-auto p-4 font-mono text-[13px] leading-relaxed relative z-10">
            {isLoading ? (
              <div className="text-slate-400 flex items-center gap-2"><RefreshCw className="w-4 h-4 animate-spin" /> Fetching logs...</div>
            ) : error ? (
              <div className="p-8">
                <div className="bg-rose-950/50 border border-rose-900 text-rose-400 p-4 rounded-md">
                  <h3 className="font-bold flex items-center gap-2"><AlertCircle className="w-5 h-5"/> Failed to load logs</h3>
                  <p className="font-mono text-sm mt-2">API: /api/v1/observability/logs</p>
                  <p className="text-sm mt-1">Reason: {error.message}</p>
                </div>
              </div>
            ) : logs?.length === 0 ? (
              <div className="text-slate-400 text-center py-20">No logs match your filters.</div>
            ) : (
              logs?.map((log) => (
                <div key={log.id} className="flex gap-4 hover:bg-slate-800/50 py-1 px-2 rounded group">
                  <span className="text-slate-500 shrink-0 select-none">
                    {new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 })}
                  </span>
                  <span className={`shrink-0 w-12 font-semibold ${getLevelColor(log.level)}`}>{log.level}</span>
                  <span className="text-indigo-400 shrink-0 w-32 truncate" title={log.service}>[{log.service}]</span>
                  <span className="text-slate-300 break-words flex-1">
                    {log.message}
                    {log.metadata?.trace_id && (
                      <span className="text-slate-500 text-[11px] ml-2 select-all">trace={log.metadata.trace_id}</span>
                    )}
                  </span>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
