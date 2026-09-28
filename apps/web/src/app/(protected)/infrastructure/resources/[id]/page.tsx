"use client";

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import useSWR from 'swr';
import { resourcesApi } from '@/lib/api/resources';
import { fetchApi } from '@/lib/api/client';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  ArrowLeft, Box, RefreshCcw, Play, Square, RotateCcw,
  Cpu, MemoryStick, Network, HardDrive, Terminal, Activity, AlertTriangle, Clock
} from 'lucide-react';
import { toast } from 'sonner';

// ─── Tabs ────────────────────────────────────────────────────────────────────
type Tab = 'overview' | 'metrics' | 'logs' | 'incidents';

// ─── Status helpers ───────────────────────────────────────────────────────────
function statusColor(status: string) {
  switch (status?.toUpperCase()) {
    case 'ACTIVE': return 'bg-emerald-500/15 text-emerald-700 border-emerald-200';
    case 'INACTIVE': return 'bg-slate-400/15 text-slate-600 border-slate-200';
    case 'FAILED': return 'bg-red-500/15 text-red-700 border-red-200';
    case 'DEGRADED': return 'bg-amber-500/15 text-amber-700 border-amber-200';
    default: return 'bg-blue-500/15 text-blue-700 border-blue-200';
  }
}

function MetricCard({ label, value, unit, icon: Icon, color }: {
  label: string; value: number | string; unit?: string; icon: any; color: string;
}) {
  return (
    <div className="bg-card border rounded-xl p-5 flex flex-col gap-2">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-bold">{value}<span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span></p>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function ResourceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>('overview');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const { data: resource, isLoading, error } = useSWR(
    id ? `/resources/${id}` : null,
    () => resourcesApi.get(id!)
  );

  const { data: metrics, mutate: refreshMetrics } = useSWR(
    tab === 'metrics' && resource?.provider === 'docker' ? `/resources/${id}/metrics` : null,
    () => fetchApi<any>(`/resources/${id}/metrics`),
    { refreshInterval: 10000 }
  );

  const { data: logsData, isLoading: logsLoading, mutate: refreshLogs } = useSWR(
    tab === 'logs' && resource?.provider === 'docker' ? `/resources/${id}/logs` : null,
    () => fetchApi<any>(`/resources/${id}/logs?tail=200`)
  );

  const { data: incidents } = useSWR(
    tab === 'incidents' ? `/incidents` : null,
    () => fetchApi<any[]>('/incidents')
  );

  const handleAction = async (action: string) => {
    setActionLoading(action);
    try {
      await fetchApi(`/resources/${id}/actions/${action}`, { method: 'POST' });
      toast.success(`Container ${action} successful`);
    } catch (e: any) {
      toast.error(`Failed to ${action}: ${e.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCcw className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }
  if (error || !resource) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <AlertTriangle className="w-10 h-10 text-destructive" />
        <p className="text-destructive font-medium">Resource not found</p>
        <Button variant="outline" onClick={() => router.back()}>Go Back</Button>
      </div>
    );
  }

  const isContainer = resource.resource_type === 'CONTAINER' && resource.provider === 'docker';
  const tabs: { id: Tab; label: string; icon: any }[] = [
    { id: 'overview', label: 'Overview', icon: Box },
    { id: 'metrics', label: 'Metrics', icon: Activity },
    { id: 'logs', label: 'Logs', icon: Terminal },
    { id: 'incidents', label: 'Incidents', icon: AlertTriangle },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div className="p-3 bg-emerald-500/10 text-emerald-600 rounded-xl">
            <Box className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">{resource.display_name || resource.name}</h1>
            <p className="text-sm text-muted-foreground font-mono">{resource.external_id}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge className={`${statusColor(resource.status)} border`}>{resource.status}</Badge>
          <Badge variant="outline">{resource.provider}</Badge>
          <Badge variant="secondary">{resource.resource_type}</Badge>
        </div>
      </div>

      {/* Container Actions */}
      {isContainer && (
        <div className="flex items-center gap-3 p-4 bg-card border rounded-xl">
          <p className="text-sm font-medium text-muted-foreground mr-2">Quick Actions:</p>
          <Button size="sm" variant="outline" onClick={() => handleAction('start')} disabled={!!actionLoading}>
            <Play className="w-3.5 h-3.5 mr-1.5 text-emerald-600" />
            {actionLoading === 'start' ? 'Starting...' : 'Start'}
          </Button>
          <Button size="sm" variant="outline" onClick={() => handleAction('restart')} disabled={!!actionLoading}>
            <RotateCcw className="w-3.5 h-3.5 mr-1.5 text-blue-600" />
            {actionLoading === 'restart' ? 'Restarting...' : 'Restart'}
          </Button>
          <Button size="sm" variant="outline" onClick={() => handleAction('stop')} disabled={!!actionLoading}>
            <Square className="w-3.5 h-3.5 mr-1.5 text-red-600" />
            {actionLoading === 'stop' ? 'Stopping...' : 'Stop'}
          </Button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t.id
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-card border rounded-xl p-6 space-y-4">
            <h3 className="font-semibold">Resource Details</h3>
            <dl className="space-y-3">
              {[
                { label: 'Name', value: resource.name },
                { label: 'Display Name', value: resource.display_name },
                { label: 'Type', value: resource.resource_type },
                { label: 'Provider', value: resource.provider },
                { label: 'Status', value: resource.status },
                { label: 'External ID', value: resource.external_id },
                { label: 'Environment', value: resource.environment_id || '—' },
                { label: 'Created', value: new Date(resource.created_at).toLocaleString() },
                { label: 'Updated', value: new Date(resource.updated_at).toLocaleString() },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between items-start gap-4">
                  <dt className="text-sm text-muted-foreground shrink-0 w-32">{label}</dt>
                  <dd className="text-sm font-mono text-right break-all">{value}</dd>
                </div>
              ))}
            </dl>
          </div>

          {resource.metadata && Object.keys(resource.metadata).length > 0 && (
            <div className="bg-card border rounded-xl p-6 space-y-4">
              <h3 className="font-semibold">Metadata</h3>
              <dl className="space-y-3">
                {Object.entries(resource.metadata).map(([k, v]) => (
                  <div key={k} className="flex justify-between items-start gap-4">
                    <dt className="text-sm text-muted-foreground shrink-0 w-32 capitalize">{k.replace(/_/g,' ')}</dt>
                    <dd className="text-sm font-mono text-right break-all">{String(v)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </div>
      )}

      {tab === 'metrics' && (
        <div className="space-y-6">
          {!isContainer ? (
            <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
              <Activity className="w-10 h-10 mb-3" />
              <p className="font-medium">Metrics only available for Docker containers</p>
            </div>
          ) : (
            <>
              <div className="flex justify-end">
                <Button size="sm" variant="outline" onClick={() => refreshMetrics()}>
                  <RefreshCcw className="w-3.5 h-3.5 mr-1.5" /> Refresh
                </Button>
              </div>
              {!metrics ? (
                <div className="text-center py-12 text-muted-foreground">Loading metrics...</div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <MetricCard label="CPU Usage" value={metrics.cpu_percent} unit="%" icon={Cpu} color="bg-blue-500/10 text-blue-600" />
                  <MetricCard label="Memory Used" value={metrics.memory_mb} unit="MB" icon={MemoryStick} color="bg-purple-500/10 text-purple-600" />
                  <MetricCard label="Memory Limit" value={metrics.memory_limit_mb} unit="MB" icon={HardDrive} color="bg-slate-500/10 text-slate-600" />
                  <MetricCard label="Memory %" value={metrics.memory_percent} unit="%" icon={Activity} color="bg-amber-500/10 text-amber-600" />
                  <MetricCard label="Net RX" value={metrics.net_rx_mb} unit="MB" icon={Network} color="bg-emerald-500/10 text-emerald-600" />
                  <MetricCard label="Net TX" value={metrics.net_tx_mb} unit="MB" icon={Network} color="bg-teal-500/10 text-teal-600" />
                  <MetricCard label="Disk Read" value={metrics.blk_read_mb} unit="MB" icon={HardDrive} color="bg-orange-500/10 text-orange-600" />
                  <MetricCard label="Disk Write" value={metrics.blk_write_mb} unit="MB" icon={HardDrive} color="bg-red-500/10 text-red-600" />
                </div>
              )}
              <p className="text-xs text-muted-foreground text-center">
                <Clock className="inline w-3 h-3 mr-1" />Auto-refreshes every 10 seconds
              </p>
            </>
          )}
        </div>
      )}

      {tab === 'logs' && (
        <div className="space-y-4">
          {!isContainer ? (
            <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
              <Terminal className="w-10 h-10 mb-3" />
              <p className="font-medium">Logs only available for Docker containers</p>
            </div>
          ) : (
            <>
              <div className="flex justify-between items-center">
                <p className="text-sm text-muted-foreground">
                  {logsData ? `${logsData.total} lines (last 200)` : ''}
                </p>
                <Button size="sm" variant="outline" onClick={() => refreshLogs()}>
                  <RefreshCcw className="w-3.5 h-3.5 mr-1.5" /> Refresh
                </Button>
              </div>
              <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-4 h-[500px] overflow-y-auto font-mono text-xs">
                {logsLoading ? (
                  <p className="text-zinc-500">Fetching logs...</p>
                ) : logsData?.lines?.length ? (
                  logsData.lines.map((line: string, i: number) => (
                    <div
                      key={i}
                      className={`py-0.5 leading-5 ${
                        line.toLowerCase().includes('error') || line.toLowerCase().includes('fatal')
                          ? 'text-red-400'
                          : line.toLowerCase().includes('warn')
                          ? 'text-amber-400'
                          : 'text-zinc-300'
                      }`}
                    >
                      {line}
                    </div>
                  ))
                ) : (
                  <p className="text-zinc-500">No logs available</p>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {tab === 'incidents' && (
        <div className="space-y-4">
          {!incidents ? (
            <p className="text-center py-12 text-muted-foreground">Loading incidents...</p>
          ) : (incidents as any[]).length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
              <AlertTriangle className="w-10 h-10 mb-3 text-emerald-500" />
              <p className="font-medium text-emerald-600">No incidents for this resource</p>
            </div>
          ) : (
            (incidents as any[]).map((incident: any) => (
              <div key={incident.id} className="bg-card border rounded-xl p-5">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold">{incident.title}</p>
                    <p className="text-sm text-muted-foreground mt-1">{incident.description || '—'}</p>
                  </div>
                  <div className="flex gap-2">
                    <Badge className={statusColor(incident.severity)}>{incident.severity}</Badge>
                    <Badge variant="outline">{incident.status}</Badge>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-3">
                  <Clock className="inline w-3 h-3 mr-1" />
                  {new Date(incident.opened_at || incident.created_at).toLocaleString()}
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
