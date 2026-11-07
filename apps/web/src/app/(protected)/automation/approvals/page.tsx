"use client";

import { useState } from 'react';
import useSWR from 'swr';
import { automationApi } from '@/lib/api/automation';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Check, X, ShieldAlert } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { toast } from 'sonner';

export default function ApprovalsPage() {
  const { data: approvals, error, isLoading, mutate } = useSWR('/automation/approvals', () => automationApi.getApprovals());
  const { hasPermission } = useAuth();
  const [busyId, setBusyId] = useState<string | null>(null);

  const handleApprove = async (id: string) => {
    setBusyId(id);
    try {
      await automationApi.approveExecution(id, 'Approved via Control Plane UI');
      toast.success('Execution approved and dispatched');
      mutate();
    } catch (err: any) {
      toast.error(`Failed to approve: ${err.message}`);
    } finally {
      setBusyId(null);
    }
  };

  const handleReject = async (id: string) => {
    setBusyId(id);
    try {
      await automationApi.rejectExecution(id, 'Rejected by operator via Control Plane UI');
      toast.success('Execution rejected');
      mutate();
    } catch (err: any) {
      toast.error(`Failed to reject: ${err.message}`);
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Human-in-the-Loop Approvals</h1>
          <p className="text-muted-foreground mt-1">Review and authorize high-risk remediation and automation actions.</p>
        </div>
      </div>

      <div className="border rounded-xl bg-card shadow-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-muted/40">
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Execution / Playbook</TableHead>
              <TableHead>Approver Role</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Requested At</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">Loading approvals...</TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-red-500">Failed to load approvals.</TableCell>
              </TableRow>
            ) : approvals?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-slate-500 py-12">
                  <ShieldAlert className="w-10 h-10 mx-auto mb-2 opacity-25" />
                  No pending or historical approvals found.
                </TableCell>
              </TableRow>
            ) : (
              approvals?.map((approval) => {
                const statusUpper = (approval.status || '').toUpperCase();
                const isPending = statusUpper === 'PENDING';
                return (
                  <TableRow key={approval.id}>
                    <TableCell className="font-mono text-xs max-w-[120px] truncate" title={approval.id}>
                      {approval.id}
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{approval.execution?.workflow?.name || 'Automation Playbook'}</div>
                      <div className="text-xs text-slate-500">Resource: {approval.execution?.resource_id || 'Global'}</div>
                    </TableCell>
                    <TableCell>{approval.approver_role || 'ADMIN'}</TableCell>
                    <TableCell>
                      <Badge variant={isPending ? 'secondary' : (statusUpper === 'APPROVED' ? 'default' : 'destructive')}>
                        {statusUpper}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500">
                      {approval.created_at ? new Date(approval.created_at).toLocaleString() : 'Just now'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end space-x-2">
                        {hasPermission('automation:approve') && isPending && (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={busyId === approval.id}
                              className="text-emerald-600 border-emerald-200 hover:bg-emerald-50"
                              onClick={() => handleApprove(approval.id)}
                            >
                              <Check className="h-4 w-4 mr-1" /> Approve
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={busyId === approval.id}
                              className="text-rose-600 border-rose-200 hover:bg-rose-50"
                              onClick={() => handleReject(approval.id)}
                            >
                              <X className="h-4 w-4 mr-1" /> Reject
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
