"use client";

import useSWR from 'swr';
import { policiesApi } from '@/lib/api/policies';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { useAuth } from '@/lib/auth';

export default function PoliciesPage() {
  const { data: policies, error, isLoading } = useSWR('/policies', () => policiesApi.list());
  const { hasPermission } = useAuth();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Policies</h1>
        {hasPermission('policies:create') && (
          <Button>
            <Plus className="mr-2 h-4 w-4" /> Create Policy
          </Button>
        )}
      </div>

      <div className="border rounded-md bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Rules</TableHead>
              <TableHead>Updated At</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">Loading policies...</TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-red-500">Failed to load policies.</TableCell>
              </TableRow>
            ) : policies?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-slate-500 py-8">No policies found.</TableCell>
              </TableRow>
            ) : (
              policies?.map((policy) => (
                <TableRow key={policy.id}>
                  <TableCell className="font-medium">{policy.name}</TableCell>
                  <TableCell className="text-slate-500 text-sm max-w-[250px] truncate">{policy.description}</TableCell>
                  <TableCell>{policy.priority}</TableCell>
                  <TableCell>
                    <Badge variant={policy.enabled ? 'default' : 'secondary'}>
                      {policy.enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </TableCell>
                  <TableCell>{policy.rules?.length || 0}</TableCell>
                  <TableCell className="text-slate-500">{new Date(policy.updated_at).toLocaleString()}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
