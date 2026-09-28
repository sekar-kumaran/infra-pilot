"use client";

import useSWR from 'swr';
import { auditApi } from '@/lib/api/audit';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

export default function AuditLogsPage() {
  const { data: logs, error, isLoading } = useSWR('/audit', () => auditApi.list());

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Audit Logs</h1>
      </div>

      <div className="border rounded-md bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Timestamp</TableHead>
              <TableHead>Actor</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Resource Type</TableHead>
              <TableHead>Resource ID</TableHead>
              <TableHead>Result</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">Loading audit logs...</TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-red-500">Failed to load audit logs.</TableCell>
              </TableRow>
            ) : logs?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-slate-500 py-8">No audit logs found.</TableCell>
              </TableRow>
            ) : (
              logs?.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-slate-500 whitespace-nowrap">{new Date(log.timestamp).toLocaleString()}</TableCell>
                  <TableCell className="font-mono text-xs">{log.actor_id || 'System'}</TableCell>
                  <TableCell className="font-medium">{log.action}</TableCell>
                  <TableCell>{log.resource_type}</TableCell>
                  <TableCell className="font-mono text-xs max-w-[120px] truncate" title={log.resource_id}>
                    {log.resource_id || '-'}
                  </TableCell>
                  <TableCell>
                    <Badge variant={log.result === 'success' ? 'outline' : 'destructive'} className={log.result === 'success' ? 'text-green-600 border-green-600' : ''}>
                      {log.result}
                    </Badge>
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
