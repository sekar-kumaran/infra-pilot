"use client";

import useSWR from 'swr';
import { environmentsApi } from '@/lib/api/environments';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { useAuth } from '@/lib/auth';

export default function EnvironmentsPage() {
  const { data: environments, error, isLoading } = useSWR('/environments', environmentsApi.list);
  const { hasPermission } = useAuth();

  if (isLoading) return <div className="p-8">Loading environments...</div>;
  if (error) return <div className="p-8 text-red-500">Failed to load environments.</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Environments</h1>
        {hasPermission('resources:create') && (
          <Button>
            <Plus className="mr-2 h-4 w-4" /> New Environment
          </Button>
        )}
      </div>

      <div className="border rounded-md bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Created At</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {environments?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-slate-500 py-12">
                  <div className="flex flex-col items-center">
                    <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center mb-3">
                      <span className="text-indigo-500 text-xl font-bold">☁️</span>
                    </div>
                    <p className="text-lg font-medium text-slate-700">No environments mapped</p>
                    <p className="text-sm">Connect a cloud provider (AWS, Azure) to auto-discover environments.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              environments?.map((env) => (
                <TableRow key={env.id}>
                  <TableCell className="font-medium">{env.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{env.environment_type}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={env.is_active ? 'default' : 'secondary'}>
                      {env.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-500">{env.description || '-'}</TableCell>
                  <TableCell className="text-slate-500">{new Date(env.created_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
