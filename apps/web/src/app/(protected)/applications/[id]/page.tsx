"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import useSWR from 'swr';
import { applicationsApi } from '@/lib/api/applications';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Box, Server, Activity, AlertTriangle, ArrowLeft, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function ApplicationDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  
  const { data: app, error: appError } = useSWR(`/applications/${params.id}`, () => applicationsApi.get(params.id));
  const { data: resources, error: resError } = useSWR(`/applications/${params.id}/resources`, () => applicationsApi.getResources(params.id));

  const getStatusColor = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'HEALTHY': return 'bg-emerald-500/10 text-emerald-500 border-emerald-200';
      case 'DEGRADED': return 'bg-amber-500/10 text-amber-500 border-amber-200';
      case 'CRITICAL': return 'bg-rose-500/10 text-rose-500 border-rose-200';
      default: return 'bg-slate-500/10 text-slate-500 border-slate-200';
    }
  };

  const getResourceStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'running':
      case 'healthy':
      case 'active':
        return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400';
      case 'stopped':
      case 'inactive':
      case 'exited':
        return 'bg-slate-500/10 text-slate-600 dark:text-slate-400';
      case 'failed':
      case 'error':
        return 'bg-rose-500/10 text-rose-600 dark:text-rose-400';
      default:
        return 'bg-blue-500/10 text-blue-600 dark:text-blue-400';
    }
  };

  if (!app) return <div className="flex items-center justify-center h-96"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-2">
        <Button variant="ghost" size="icon" onClick={() => router.back()} className="h-8 w-8 text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 text-indigo-600 rounded-xl">
              <Box className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-3">
                {app.name}
                <Badge variant="outline" className={getStatusColor(app.status)}>{app.status}</Badge>
              </h1>
              <p className="text-muted-foreground text-sm mt-0.5">{app.description || 'No description provided'}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="col-span-1 md:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle>Application Resources</CardTitle>
              <CardDescription>All underlying infrastructure components</CardDescription>
            </div>
            <Button size="sm" variant="outline" className="h-8">
              <Plus className="w-3.5 h-3.5 mr-1" /> Add Resource
            </Button>
          </CardHeader>
          <CardContent>
            {resources?.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground bg-muted/20 rounded-lg border border-dashed border-border mt-4">
                <Server className="w-10 h-10 mx-auto opacity-20 mb-3" />
                <p>No resources have been assigned to this application yet.</p>
                <p className="text-xs mt-1">Edit a resource and set its application_id to link it.</p>
              </div>
            ) : (
              <div className="mt-4 border rounded-xl overflow-hidden">
                <Table>
                  <TableHeader className="bg-muted/50">
                    <TableRow>
                      <TableHead>Resource</TableHead>
                      <TableHead>Provider</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>State</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {resources?.map(resource => (
                      <TableRow 
                        key={resource.id}
                        className="cursor-pointer hover:bg-muted/30 transition-colors"
                        onClick={() => router.push(`/infrastructure/resources/${resource.id}`)}
                      >
                        <TableCell className="font-medium text-foreground">
                          {resource.display_name || resource.name}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                            <Server className="w-3.5 h-3.5" />
                            {resource.provider.toUpperCase()}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="font-mono text-[10px] bg-muted/30">{resource.resource_type}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={getResourceStatusColor(resource.status)} variant="secondary">
                            {resource.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-500" />
                App Health Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-foreground">
                {app.status === 'HEALTHY' ? '100' : app.status === 'DEGRADED' ? '65' : '10'}
                <span className="text-xl text-muted-foreground font-normal">/100</span>
              </div>
              <div className="mt-4 h-2 w-full bg-secondary rounded-full overflow-hidden">
                <div 
                  className={`h-full ${app.status === 'HEALTHY' ? 'bg-emerald-500' : app.status === 'DEGRADED' ? 'bg-amber-500' : 'bg-rose-500'}`} 
                  style={{ width: app.status === 'HEALTHY' ? '100%' : app.status === 'DEGRADED' ? '65%' : '10%' }}
                />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-500" />
                Active Incidents
              </CardTitle>
            </CardHeader>
            <CardContent>
              {app.incidents_count === 0 ? (
                <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-medium">
                  All clear. No active incidents.
                </div>
              ) : (
                <div className="flex items-center gap-2 text-rose-600 dark:text-rose-400 font-bold text-2xl">
                  {app.incidents_count} Open Incident{app.incidents_count !== 1 ? 's' : ''}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
