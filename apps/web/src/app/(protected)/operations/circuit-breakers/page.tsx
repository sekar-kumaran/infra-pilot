"use client";

import useSWR from 'swr';
import { integrationsApi } from '@/lib/api/integrations';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Clock, Activity, PowerOff, ShieldCheck } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { toast } from 'sonner';

export default function CircuitBreakersPage() {
  const { data: integrations, error, isLoading, mutate } = useSWR('/integrations', integrationsApi.list, { refreshInterval: 5000 });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Circuit Breakers</h1>
        <Card>
          <CardHeader>
            <CardTitle>Provider States</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[1,2,3].map(i => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-red-500">
        <AlertTriangle className="h-8 w-8 mb-4" />
        Failed to load circuit breakers: {error.message}
      </div>
    );
  }

  const renderStateBadge = (state: string) => {
    switch(state) {
      case 'CLOSED':
        return <Badge className="bg-green-100 text-green-800 border-green-200"><ShieldCheck className="h-3 w-3 mr-1" /> Closed (Healthy)</Badge>;
      case 'OPEN':
        return <Badge variant="destructive"><PowerOff className="h-3 w-3 mr-1" /> Open (Failing)</Badge>;
      case 'HALF_OPEN':
        return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200"><Activity className="h-3 w-3 mr-1" /> Half Open (Testing)</Badge>;
      default:
        return <Badge variant="outline">{state}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Circuit Breakers</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Provider Integration States</CardTitle>
        </CardHeader>
        <CardContent>
          {!integrations || integrations.length === 0 ? (
            <div className="text-center py-8 text-slate-500">No integrations found.</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Provider</TableHead>
                  <TableHead>Integration Name</TableHead>
                  <TableHead>Circuit State</TableHead>
                  <TableHead>Failure Count</TableHead>
                  <TableHead>Last Failure</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {integrations.map((integration) => (
                  <TableRow key={integration.id}>
                    <TableCell className="font-medium capitalize">{integration.provider}</TableCell>
                    <TableCell>{integration.name}</TableCell>
                    <TableCell>{renderStateBadge(integration.circuit_state)}</TableCell>
                    <TableCell>{integration.failure_count}</TableCell>
                    <TableCell>
                      {integration.last_failure_at ? (
                        <div className="flex items-center text-sm text-slate-500">
                          <Clock className="mr-2 h-4 w-4" />
                          {new Date(integration.last_failure_at).toLocaleString()}
                        </div>
                      ) : (
                        <span className="text-slate-400">Never</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
