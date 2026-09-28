"use client";

import useSWR from 'swr';
import { incidentsApi } from '@/lib/api/incidents';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useAuth } from '@/lib/auth';
import { toast } from 'sonner';
import { Activity, AlertCircle, ArrowLeft, Server, Shield, CheckCircle2, AlertTriangle, Workflow } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { Progress } from '@/components/ui/progress';

export default function IncidentDetailsPage() {
  const params = useParams();
  const id = params.id as string;
  const { data: incident, error, isLoading, mutate } = useSWR(`/incidents/${id}`, () => incidentsApi.get(id));
  const { hasPermission } = useAuth();

  const handleAcknowledge = async () => {
    try {
      await incidentsApi.acknowledge(id);
      toast.success('Incident acknowledged');
      mutate();
    } catch (err: any) {
      toast.error(`Failed to acknowledge: ${err.message}`);
    }
  };

  const handleResolve = async () => {
    if (!confirm('Are you sure you want to resolve this incident?')) return;
    try {
      await incidentsApi.resolve(id);
      toast.success('Incident resolved');
      mutate();
    } catch (err: any) {
      toast.error(`Failed to resolve: ${err.message}`);
    }
  };

  if (isLoading) return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
      <Activity className="w-8 h-8 animate-spin text-indigo-500" />
      <p className="text-muted-foreground animate-pulse">Loading incident telemetry...</p>
    </div>
  );
  if (error || !incident) return <div className="p-8 text-destructive text-center">Failed to load incident details.</div>;

  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'bg-red-500/15 text-red-700 border-none shadow-sm';
      case 'high': return 'bg-orange-500/15 text-orange-700 border-none shadow-sm';
      case 'medium': return 'bg-yellow-500/15 text-yellow-700 border-none shadow-sm';
      case 'low': return 'bg-blue-500/15 text-blue-700 border-none shadow-sm';
      default: return 'bg-slate-500/15 text-slate-700 border-none shadow-sm';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'open': return 'bg-red-500 text-white';
      case 'acknowledged': return 'bg-amber-500 text-white';
      case 'remediation_running':
      case 'remediating': return 'bg-blue-500 text-white animate-pulse';
      case 'verifying': return 'bg-purple-500 text-white animate-pulse';
      case 'recovered':
      case 'resolved':
      case 'closed': return 'bg-emerald-500 text-white';
      case 'escalated': return 'bg-rose-600 text-white';
      default: return 'bg-slate-500 text-white';
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-4">
          <Link href="/incidents">
            <Button variant="outline" size="icon" className="h-10 w-10 rounded-full bg-card hover:bg-muted shadow-sm">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-500 dark:from-white dark:to-slate-400">
              {incident.title}
            </h1>
            <p className="text-muted-foreground mt-1 flex items-center gap-2">
              <Badge variant="outline" className="font-mono text-[10px]">{id.split('-')[0]}</Badge>
              • {new Date(incident.opened_at).toLocaleString()}
            </p>
          </div>
        </div>
        
        <div className="flex space-x-2">
          {hasPermission('incidents:update') && incident.status?.toLowerCase() === 'open' && (
            <Button onClick={handleAcknowledge} className="bg-amber-500 hover:bg-amber-600 text-white shadow-md">
              Acknowledge
            </Button>
          )}
          {hasPermission('incidents:update') && !['resolved', 'closed', 'recovered'].includes(incident.status?.toLowerCase()) && (
            <Button variant="outline" onClick={handleResolve} className="border-emerald-500 text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/30">
              Mark Resolved
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-muted/40 bg-card/40 backdrop-blur-md shadow-sm">
            <CardHeader className="pb-4 border-b border-border/50 bg-muted/10">
              <div className="flex justify-between items-start">
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-indigo-500" />
                  Situation Report
                </CardTitle>
                <div className="flex gap-2">
                  <Badge className={getSeverityColor(incident.severity)}>{incident.severity}</Badge>
                  <Badge className={getStatusColor(incident.status)}>{incident.status}</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              <div className="bg-muted/30 p-4 rounded-xl border border-muted/50 text-slate-700 dark:text-slate-300">
                {incident.description || 'No detailed description provided by the detection source.'}
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
                <div className="p-3 bg-muted/20 rounded-lg">
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Resource</div>
                  <div className="font-medium capitalize text-xs truncate" title={incident.primary_resource_id}>{incident.primary_resource_id || 'Global'}</div>
                </div>
                <div className="p-3 bg-muted/20 rounded-lg">
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Priority</div>
                  <div className="font-medium">{incident.priority}</div>
                </div>
                <div className="p-3 bg-muted/20 rounded-lg">
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Severity</div>
                  <div className="font-medium">{incident.severity || 'N/A'}</div>
                </div>
                <div className="p-3 bg-muted/20 rounded-lg">
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Resolved At</div>
                  <div className="font-medium">{incident.resolved_at ? new Date(incident.resolved_at).toLocaleString() : 'Pending'}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timeline */}
          <Card className="border-muted/40 shadow-sm overflow-hidden">
            <CardHeader className="bg-muted/10 border-b border-border/50">
              <CardTitle className="flex items-center text-lg"><Activity className="h-5 w-5 mr-2 text-indigo-500" /> Audit Trail</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              {incident.events?.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">No events recorded.</div>
              ) : (
                <div className="space-y-0">
                  {incident.events?.map((event: any, i: number) => (
                    <div key={event.id} className="flex gap-4 group">
                      <div className="flex flex-col items-center">
                        <div className="h-2.5 w-2.5 bg-indigo-500/80 rounded-full mt-1.5 ring-4 ring-indigo-50 dark:ring-indigo-950" />
                        {i !== incident.events.length - 1 && (
                          <div className="h-full w-px bg-border/80 my-1 group-hover:bg-indigo-300 transition-colors" />
                        )}
                      </div>
                      <div className="pb-6">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-800 dark:text-slate-200">{event.event_type}</span>
                          <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full font-mono">{new Date(event.created_at).toLocaleTimeString()}</span>
                        </div>
                        <div className="text-slate-600 dark:text-slate-400 mt-1">{event.message}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          
          {/* Active Workflows */}
          <Card className="border-muted/40 shadow-sm border-indigo-200 dark:border-indigo-900/50">
            <CardHeader className="bg-indigo-50/50 dark:bg-indigo-950/20 pb-4 border-b border-border/50">
              <CardTitle className="flex items-center text-lg text-indigo-800 dark:text-indigo-300">
                <Workflow className="h-5 w-5 mr-2" /> Orchestration
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="text-center p-4">
                <Link href="/automation/executions">
                  <Button variant="outline" className="w-full justify-between group border-indigo-200 hover:bg-indigo-50 dark:hover:bg-indigo-900/30">
                    View Associated Executions
                    <ArrowLeft className="w-4 h-4 rotate-180 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Related Alerts */}
          <Card className="border-muted/40 shadow-sm">
            <CardHeader className="bg-muted/10 pb-4 border-b border-border/50">
              <CardTitle className="flex items-center text-lg"><AlertCircle className="h-5 w-5 mr-2 text-rose-500" /> Correlated Alerts</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              {incident.alerts?.length === 0 ? (
                <p className="text-sm text-center py-4 text-muted-foreground">No telemetry alerts.</p>
              ) : (
                incident.alerts?.map((alert: any) => (
                  <div key={alert.id} className="text-sm p-3 border border-border/50 rounded-xl bg-card hover:bg-muted/20 transition-colors">
                    <div className="font-semibold text-slate-800 dark:text-slate-200 line-clamp-2">{alert.title}</div>
                    <div className="flex justify-between items-center mt-3">
                      <Badge variant="secondary" className="text-[10px] uppercase font-semibold tracking-wider bg-rose-500/10 text-rose-600">{alert.status}</Badge>
                      <span className="text-muted-foreground text-[10px] uppercase font-semibold flex items-center gap-1">
                        <Server className="w-3 h-3" /> {alert.provider}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Related Resources */}
          <Card className="border-muted/40 shadow-sm">
            <CardHeader className="bg-muted/10 pb-4 border-b border-border/50">
              <CardTitle className="flex items-center text-lg"><Server className="h-5 w-5 mr-2 text-emerald-500" /> Affected Infrastructure</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              {incident.resources?.length === 0 ? (
                <p className="text-sm text-center py-4 text-muted-foreground">No resources identified.</p>
              ) : (
                incident.resources?.map((resource: any) => (
                  <div key={resource.id} className="text-sm p-3 border border-border/50 rounded-xl bg-card hover:bg-muted/20 transition-colors">
                    <div className="font-semibold text-slate-800 dark:text-slate-200 truncate" title={resource.display_name}>{resource.display_name}</div>
                    <div className="flex justify-between items-center mt-3">
                      <Badge variant="outline" className="text-[10px] font-mono bg-background">{resource.resource_type}</Badge>
                      <span className="text-muted-foreground text-[10px] uppercase font-semibold">
                        {resource.provider}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
