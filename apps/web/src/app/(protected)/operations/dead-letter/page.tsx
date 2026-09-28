"use client";

import useSWR from 'swr';
import { automationApi } from '@/lib/api/automation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Clock, RefreshCw } from 'lucide-react';
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

export default function DeadLetterPage() {
  const { data: executions, error, isLoading, mutate } = useSWR('/workflows/executions', automationApi.getExecutions, { refreshInterval: 10000 });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Dead Letter Queue</h1>
        <Card>
          <CardHeader>
            <CardTitle>Failed Executions</CardTitle>
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
        Failed to load dead letter queue: {error.message}
      </div>
    );
  }

  const deadLetters = executions?.filter(e => e.status === 'DEAD_LETTERED') || [];

  const handleRetry = async (id: string) => {
    try {
      await fetch(`/api/v1/workflows/executions/${id}/resume`, { method: 'POST' });
      toast.success('Retry initiated');
      mutate();
    } catch (err: any) {
      toast.error(`Retry failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Dead Letter Queue</h1>
        <Badge variant="destructive" className="text-lg px-4 py-1">
          {deadLetters.length} Unrecoverable Failures
        </Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Failed Executions</CardTitle>
        </CardHeader>
        <CardContent>
          {deadLetters.length === 0 ? (
            <div className="text-center py-12">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <p className="text-lg font-medium text-slate-700">Queue is empty</p>
              <p className="text-slate-500">No dead-lettered executions found.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Workflow ID</TableHead>
                  <TableHead>Resource ID</TableHead>
                  <TableHead>Error Classification</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Attempts</TableHead>
                  <TableHead>Failed At</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {deadLetters.map((dl) => (
                  <TableRow key={dl.id}>
                    <TableCell className="font-mono text-xs">{dl.workflow_id}</TableCell>
                    <TableCell className="font-mono text-xs">{dl.resource_id || 'N/A'}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{dl.error_classification || 'UNKNOWN'}</Badge>
                    </TableCell>
                    <TableCell className="max-w-md truncate" title={dl.failure_reason}>
                      {dl.failure_reason || 'No specific reason provided'}
                    </TableCell>
                    <TableCell>{dl.retry_count}</TableCell>
                    <TableCell>
                      <div className="flex items-center text-sm text-slate-500">
                        <Clock className="mr-2 h-4 w-4" />
                        {new Date(dl.completed_at || dl.updated_at).toLocaleString()}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="outline" size="sm" onClick={() => handleRetry(dl.id)}>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Retry
                      </Button>
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

function CheckCircle(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}
