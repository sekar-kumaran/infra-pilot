"use client";

import useSWR from 'swr';
import { automationApi } from '@/lib/api/automation';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Check, X } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { toast } from 'sonner';

export default function ApprovalsPage() {
  const { data: approvals, error, isLoading, mutate } = useSWR('/automation/approvals', () => automationApi.getApprovals());
  const { hasPermission } = useAuth();

  const handleApprove = async (id: string) => {
    if (!confirm('Approve this automation execution?')) return;
    try {
      await automationApi.approveExecution(id);
      toast.success('Execution approved');
      mutate();
    } catch (err: any) {
      toast.error(`Failed to approve: ${err.message}`);
    }
  };

  const handleReject = async (id: string) => {
    const reason = prompt('Please enter a reason for rejection:');
    if (reason === null) return;
    try {
      await automationApi.rejectExecution(id, reason || 'Rejected via console');
      toast.success('Execution rejected');
      mutate();
    } catch (err: any) {
      toast.error(`Failed to reject: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Approvals</h1>
      </div>

      <div className="border rounded-md bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Execution/Playbook</TableHead>
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
                <TableCell colSpan={6} className="text-center text-slate-500 py-8">No approvals found.</TableCell>
              </TableRow>
            ) : (
              approvals?.map((approval) => (
                <TableRow key={approval.id}>
                  <TableCell className="font-mono text-xs max-w-[120px] truncate" title={approval.id}>
                    {approval.id}
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">{approval.execution?.workflow?.name || 'Unknown Workflow'}</div>
                    <div className="text-xs text-slate-500">Resource: {approval.execution?.resource_id || 'Global'}</div>
                  </TableCell>
                  <TableCell>{approval.approver_role}</TableCell>
                  <TableCell>
                    <Badge variant={approval.status === 'pending' ? 'secondary' : (approval.status === 'approved' ? 'default' : 'destructive')}>
                      {approval.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-500">{new Date(approval.created_at).toLocaleString()}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end space-x-2">
                      {hasPermission('automation:approve') && approval.status === 'pending' && (
                        <>
                          <Button 
                            variant="outline" 
                            size="sm"
                            className="text-green-600 hover:text-green-700 hover:bg-green-50"
                            onClick={() => handleApprove(approval.id)}
                          >
                            <Check className="h-4 w-4 mr-1" /> Approve
                          </Button>
                          <Button 
                            variant="outline" 
                            size="sm"
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            onClick={() => handleReject(approval.id)}
                          >
                            <X className="h-4 w-4 mr-1" /> Reject
                          </Button>
                        </>
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
