"use client";

import useSWR from 'swr';
import { incidentsApi } from '@/lib/api/incidents';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ExternalLink, AlertTriangle, ShieldAlert } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import Link from 'next/link';

export default function IncidentsPage() {
  const { data: incidents, error, isLoading } = useSWR('/incidents', () => incidentsApi.list());
  const { hasPermission } = useAuth();

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
      case 'open': return 'bg-red-500/20 text-red-700 font-semibold border-none';
      case 'acknowledged': return 'bg-amber-500/20 text-amber-700 font-semibold border-none';
      case 'remediation_running':
      case 'remediating': return 'bg-blue-500/20 text-blue-700 font-semibold border-none animate-pulse';
      case 'verifying': return 'bg-purple-500/20 text-purple-700 font-semibold border-none animate-pulse';
      case 'recovered':
      case 'resolved':
      case 'closed': return 'bg-emerald-500/20 text-emerald-700 font-semibold border-none';
      case 'escalated': return 'bg-rose-600/20 text-rose-700 font-semibold border-none';
      default: return 'bg-slate-500/20 text-slate-700 font-semibold border-none';
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-red-500 to-orange-600">
            Active Incidents
          </h1>
          <p className="text-muted-foreground mt-2 text-lg">
            Monitor and resolve issues identified by the correlation engine.
          </p>
        </div>
      </div>

      <div className="border border-border/50 rounded-xl bg-card/40 backdrop-blur-md shadow-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-muted/30">
            <TableRow className="hover:bg-transparent">
              <TableHead className="font-semibold">Incident ID</TableHead>
              <TableHead className="font-semibold">Title</TableHead>
              <TableHead className="font-semibold">Severity</TableHead>
              <TableHead className="font-semibold">Status</TableHead>
              <TableHead className="font-semibold">Opened At</TableHead>
              <TableHead className="text-right font-semibold">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                  <div className="flex flex-col items-center justify-center">
                    <ShieldAlert className="w-8 h-8 animate-pulse text-indigo-400 mb-2" />
                    Loading incidents...
                  </div>
                </TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-destructive bg-destructive/5">
                  Failed to load incidents.
                </TableCell>
              </TableRow>
            ) : incidents?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-slate-500 py-12">No active incidents found.</TableCell>
              </TableRow>
            ) : (
              incidents?.map((incident: any) => (
                <TableRow key={incident.id} className="hover:bg-muted/20 transition-colors">
                  <TableCell className="font-mono text-xs text-muted-foreground">{incident.id.substring(0, 8)}</TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      <span className="font-bold text-foreground line-clamp-1">{incident.title}</span>
                      <span className="text-xs text-muted-foreground">Priority: {incident.priority}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={getSeverityColor(incident.severity)}>
                      {incident.severity}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={getStatusColor(incident.status)}>
                      {incident.status?.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(incident.opened_at).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <Link href={`/incidents/${incident.id}`}>
                      <Button variant="ghost" size="sm" className="hover:bg-indigo-50 dark:hover:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
                        View Details <ExternalLink className="h-4 w-4 ml-1" />
                      </Button>
                    </Link>
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
