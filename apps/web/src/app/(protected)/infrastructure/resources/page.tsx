"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import useSWR from 'swr';
import { resourcesApi } from '@/lib/api/resources';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, Server, Box, Activity, ChevronRight, Filter } from 'lucide-react';

export default function ResourcesPage() {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [providerFilter, setProviderFilter] = useState('');
  
  // Use SWR to fetch resources (server-side pagination would pass page params here)
  const { data: resources, error, isLoading } = useSWR('/resources', () => resourcesApi.list());

  const allProviders = Array.from(new Set(resources?.map(r => r.provider) || []));

  const filteredResources = resources?.filter(r => {
    const matchSearch = !search ||
      r.name.toLowerCase().includes(search.toLowerCase()) || 
      (r.display_name || '').toLowerCase().includes(search.toLowerCase()) ||
      r.provider.toLowerCase().includes(search.toLowerCase()) ||
      r.resource_type.toLowerCase().includes(search.toLowerCase());
    const matchProvider = !providerFilter || r.provider === providerFilter;
    return matchSearch && matchProvider;
  });

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
      case 'running': return 'bg-emerald-500/15 text-emerald-700 border-none';
      case 'stopped':
      case 'terminated': return 'bg-slate-500/15 text-slate-700 border-none';
      case 'failed':
      case 'error': return 'bg-red-500/15 text-red-700 border-none';
      default: return 'bg-blue-500/15 text-blue-700 border-none';
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-teal-600">
            Infrastructure Graph
          </h1>
          <p className="text-muted-foreground mt-2 text-lg">
            Discovered resources and entities across all connected providers.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
          <Input 
            placeholder="Search resources, types, or providers..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-10 bg-card/50"
          />
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant={providerFilter === '' ? 'default' : 'outline'}
            onClick={() => setProviderFilter('')}
          >All</Button>
          {allProviders.map(p => (
            <Button
              key={p}
              size="sm"
              variant={providerFilter === p ? 'default' : 'outline'}
              onClick={() => setProviderFilter(p)}
              className="capitalize"
            >{p}</Button>
          ))}
        </div>
        <p className="text-sm text-muted-foreground ml-auto">{filteredResources?.length ?? 0} resources</p>
      </div>

      <div className="border border-border/50 rounded-xl bg-card/40 backdrop-blur-md shadow-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-muted/30">
            <TableRow className="hover:bg-transparent">
              <TableHead className="font-semibold w-[300px]">Display Name</TableHead>
              <TableHead className="font-semibold">Type</TableHead>
              <TableHead className="font-semibold">Provider</TableHead>
              <TableHead className="font-semibold">State</TableHead>
              <TableHead className="font-semibold">Last Updated</TableHead>
              <TableHead className="w-8"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-12 text-muted-foreground">
                  <div className="flex flex-col items-center justify-center">
                    <Activity className="w-8 h-8 animate-pulse text-emerald-400 mb-2" />
                    Discovering resources...
                  </div>
                </TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-destructive bg-destructive/5">
                  Failed to synchronize resources.
                </TableCell>
              </TableRow>
            ) : filteredResources?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-slate-500 py-12">
                  <div className="flex flex-col items-center">
                    <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center mb-3 text-emerald-500">
                      <Box className="w-6 h-6" />
                    </div>
                    <p className="text-lg font-medium text-slate-700">No resources discovered</p>
                    <p className="text-sm">Connect an infrastructure provider (Kubernetes, AWS) to sync your resources.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              filteredResources?.map((resource) => (
                <TableRow
                  key={resource.id}
                  className="hover:bg-muted/30 transition-colors cursor-pointer"
                  onClick={() => router.push(`/infrastructure/resources/${resource.id}`)}
                >
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-emerald-500/10 text-emerald-600 rounded-lg">
                        <Box className="w-4 h-4" />
                      </div>
                      <div className="flex flex-col">
                        <span className="font-semibold text-foreground line-clamp-1" title={resource.display_name || resource.name}>{resource.display_name || resource.name}</span>
                        <span className="text-xs text-muted-foreground font-mono truncate max-w-[260px]" title={resource.name}>{resource.name}</span>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="font-mono text-[10px] bg-muted/50">
                      {resource.resource_type}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1.5 text-sm font-medium">
                      <Server className="w-3.5 h-3.5 text-muted-foreground" />
                      {resource.provider.toUpperCase()}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(resource.status)}>
                      {resource.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(resource.updated_at).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
