"use client";

import useSWR from 'swr';
import { alertsApi, AlertResponse } from '@/lib/api/alerts';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Check, CheckCircle2 } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { toast } from 'sonner';

export default function AlertsPage() {
  const { data: alerts, error, isLoading, mutate } = useSWR('/alerts', () => alertsApi.list());
  const { hasPermission } = useAuth();

  const handleAcknowledge = async (id: string) => {
    try {
      await alertsApi.acknowledge(id);
      toast.success('Alert acknowledged');
      mutate();
    } catch (err: any) {
      toast.error(`Failed to acknowledge: ${err.message}`);
    }
  };

  const handleResolve = async (id: string) => {
    if (!confirm('Are you sure you want to resolve this alert?')) return;
    try {
      await alertsApi.resolve(id);
      toast.success('Alert resolved');
      mutate();
    } catch (err: any) {
      toast.error(`Failed to resolve: ${err.message}`);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-blue-500';
      default: return 'bg-slate-500';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Alerts</h1>
      </div>

      <div className="border rounded-md bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Provider</TableHead>
              <TableHead>Started At</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">Loading alerts...</TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-red-500">Failed to load alerts.</TableCell>
              </TableRow>
            ) : alerts?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-slate-500 py-12">
                  <div className="flex flex-col items-center">
                    <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center mb-3">
                      <span className="text-orange-500 text-xl font-bold">!</span>
                    </div>
                    <p className="text-lg font-medium text-slate-700">No active alerts</p>
                    <p className="text-sm">Connect a monitoring provider (Prometheus, Datadog) to receive alerts.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              alerts?.map((alert) => (
                <TableRow key={alert.id}>
                  <TableCell className="font-medium">{alert.title}</TableCell>
                  <TableCell>
                    <Badge className={getSeverityColor(alert.severity)}>
                      {alert.severity}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{alert.status}</Badge>
                  </TableCell>
                  <TableCell>{alert.provider}</TableCell>
                  <TableCell className="text-slate-500">{new Date(alert.started_at).toLocaleString()}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end space-x-2">
                      {hasPermission('alerts:update') && alert.status === 'open' && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleAcknowledge(alert.id)}
                        >
                          <Check className="h-4 w-4 mr-1" /> Ack
                        </Button>
                      )}
                      {hasPermission('alerts:update') && (alert.status === 'open' || alert.status === 'acknowledged') && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          className="text-green-600 hover:text-green-700 hover:bg-green-50"
                          onClick={() => handleResolve(alert.id)}
                        >
                          <CheckCircle2 className="h-4 w-4 mr-1" /> Resolve
                        </Button>
                      )}
                    </div>
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
