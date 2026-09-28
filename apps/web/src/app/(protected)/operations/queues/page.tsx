"use client";

import useSWR from 'swr';
import { operationsApi } from '@/lib/api/operations';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, AlertTriangle, PlaySquare, CheckCircle, Clock } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export default function QueuesPage() {
  const { data: queues, error, isLoading } = useSWR('/operations/queues', operationsApi.getQueues, { refreshInterval: 5000 });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Queues</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-32 w-full" />)}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-red-500">
        <AlertTriangle className="h-8 w-8 mb-4" />
        Failed to load queues: {error.message}
      </div>
    );
  }

  const defaultQueue = queues?.find(q => q.queue_name === 'celery');

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Message Queues</h1>
      
      {defaultQueue && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Tasks</CardTitle>
              <Clock className="h-4 w-4 text-slate-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{defaultQueue.pending_tasks}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
              <PlaySquare className="h-4 w-4 text-indigo-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{defaultQueue.active_tasks}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Reserved Tasks</CardTitle>
              <Activity className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{defaultQueue.reserved_tasks}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Workers</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{defaultQueue.worker_count}</div>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>All Queues</CardTitle>
        </CardHeader>
        <CardContent>
          {queues?.length === 0 ? (
            <div className="text-center py-8 text-slate-500">No queues active.</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Queue Name</TableHead>
                  <TableHead>Workers</TableHead>
                  <TableHead>Active Tasks</TableHead>
                  <TableHead>Reserved Tasks</TableHead>
                  <TableHead>Pending Tasks</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {queues?.map((q) => (
                  <TableRow key={q.queue_name}>
                    <TableCell className="font-medium">{q.queue_name}</TableCell>
                    <TableCell>{q.worker_count}</TableCell>
                    <TableCell>{q.active_tasks}</TableCell>
                    <TableCell>{q.reserved_tasks}</TableCell>
                    <TableCell>{q.pending_tasks}</TableCell>
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
