"use client";

import useSWR from 'swr';
import { fetchApi } from '@/lib/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertTriangle, Code, TerminalSquare } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface ProviderCapabilityRegistryEntry {
  provider: string;
  display_name: string;
  version: string;
  status: string;
  capabilities: string[];
  resources: string[];
  read_operations: string[];
  mutation_operations: string[];
  authentication_requirements: string[];
}

export default function ActionsPage() {
  const { data: capabilities, error, isLoading } = useSWR('/providers/capabilities', () => fetchApi<ProviderCapabilityRegistryEntry[]>('/providers/capabilities'));

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Automation Actions</h1>
        <Card>
          <CardHeader>
            <CardTitle>Available Actions</CardTitle>
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
        Failed to load actions: {error.message}
      </div>
    );
  }

  // Flatten the capabilities into a list of actions
  const actions: { provider: string; name: string; type: 'read' | 'mutation' }[] = [];
  
  capabilities?.forEach(cap => {
    cap.read_operations.forEach(op => {
      actions.push({ provider: cap.provider, name: op, type: 'read' });
    });
    cap.mutation_operations.forEach(op => {
      actions.push({ provider: cap.provider, name: op, type: 'mutation' });
    });
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Automation Actions</h1>
        <Badge variant="outline" className="text-sm px-3 py-1">
          {actions.length} Total Actions Registered
        </Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Action Registry</CardTitle>
        </CardHeader>
        <CardContent>
          {actions.length === 0 ? (
            <div className="text-center py-12">
              <TerminalSquare className="h-12 w-12 text-slate-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-slate-700">No actions found</p>
              <p className="text-slate-500">Connect a provider to load its capabilities.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Provider</TableHead>
                  <TableHead>Action Name</TableHead>
                  <TableHead>Type</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {actions.map((action, idx) => (
                  <TableRow key={`${action.provider}-${action.name}-${idx}`}>
                    <TableCell className="font-medium capitalize">{action.provider}</TableCell>
                    <TableCell className="font-mono text-sm flex items-center">
                      <Code className="h-4 w-4 mr-2 text-slate-500" />
                      {action.name}
                    </TableCell>
                    <TableCell>
                      <Badge variant={action.type === 'mutation' ? 'destructive' : 'secondary'} className={action.type === 'mutation' ? '' : 'bg-blue-100 text-blue-800'}>
                        {action.type.toUpperCase()}
                      </Badge>
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
