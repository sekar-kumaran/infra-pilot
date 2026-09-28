"use client";

import useSWR from 'swr';
import { automationApi } from '@/lib/api/automation';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { PlayCircle, Clock, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

export default function ExecutionsPage() {
  // Use a wrapper or change typing slightly if workflow response differs slightly from playbook response
  const { data: executions, error, isLoading } = useSWR('/workflows/executions', () => automationApi.getExecutions());

  const getStatusInfo = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'succeeded':
      case 'completed': return { color: 'bg-emerald-500/15 text-emerald-700 border-none', icon: <CheckCircle2 className="w-3 h-3 mr-1" /> };
      case 'failed': return { color: 'bg-destructive/15 text-destructive border-none', icon: <XCircle className="w-3 h-3 mr-1" /> };
      case 'running': return { color: 'bg-blue-500/15 text-blue-700 border-none', icon: <PlayCircle className="w-3 h-3 mr-1 animate-pulse" /> };
      case 'waiting_approval': return { color: 'bg-amber-500/15 text-amber-700 border-none', icon: <Clock className="w-3 h-3 mr-1" /> };
      case 'verifying': return { color: 'bg-purple-500/15 text-purple-700 border-none', icon: <AlertTriangle className="w-3 h-3 mr-1" /> };
      default: return { color: 'outline', icon: null };
    }
  };

  const getProgress = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'pending': return 10;
      case 'waiting_approval': return 30;
      case 'running': return 60;
      case 'verifying': return 85;
      case 'succeeded':
      case 'completed': return 100;
      case 'failed': return 100; // Complete but failed
      default: return 0;
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-500 to-indigo-600">
            Execution Timeline
          </h1>
          <p className="text-muted-foreground mt-2 text-lg">
            Monitor autonomous operations, approvals, and workflow verifications.
          </p>
        </div>
      </div>

      <div className="border border-border/50 rounded-xl bg-card/40 backdrop-blur-md shadow-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-muted/30">
            <TableRow className="hover:bg-transparent">
              <TableHead className="font-semibold">Execution ID</TableHead>
              <TableHead className="font-semibold">Workflow / Target</TableHead>
              <TableHead className="font-semibold w-[200px]">Progress</TableHead>
              <TableHead className="font-semibold">Status</TableHead>
              <TableHead className="font-semibold">Started At</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-12 text-muted-foreground">
                  <div className="flex flex-col items-center justify-center">
                    <PlayCircle className="w-8 h-8 animate-pulse text-indigo-400 mb-2" />
                    Loading execution timeline...
                  </div>
                </TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-destructive bg-destructive/5">
                  Failed to load executions.
                </TableCell>
              </TableRow>
            ) : executions?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-slate-500 py-12">No active executions.</TableCell>
              </TableRow>
            ) : (
              executions?.map((execution: any) => {
                const sInfo = getStatusInfo(execution.status);
                const isFailed = execution.status?.toLowerCase() === 'failed';
                
                return (
                  <TableRow key={execution.id} className="hover:bg-muted/20 transition-colors">
                    <TableCell className="font-mono text-xs text-muted-foreground" title={execution.id}>
                      {execution.id.split('-')[0]}...
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        <span className="font-bold text-foreground">
                          {execution.workflow?.name || execution.workflow_id || 'Unknown Workflow'}
                        </span>
                        {execution.resource_id && (
                          <span className="text-xs text-muted-foreground flex items-center gap-1">
                            Target ID: <span className="font-mono">{execution.resource_id.split('-')[0]}</span>
                          </span>
                        )}
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="flex flex-col gap-2 pr-4">
                        <Progress 
                          value={getProgress(execution.status)} 
                          className={`h-2 ${isFailed ? 'bg-destructive/20 *:bg-destructive' : 'bg-indigo-500/20 *:bg-indigo-500'}`} 
                        />
                        <span className="text-[10px] uppercase font-semibold text-muted-foreground">
                          {execution.current_step_id ? 'Executing Step...' : 'Processing'}
                        </span>
                      </div>
                    </TableCell>

                    <TableCell>
                      <Badge variant="outline" className={`font-medium px-2.5 py-0.5 ${sInfo.color}`}>
                        {sInfo.icon}
                        {execution.status}
                      </Badge>
                      {execution.failure_reason && (
                        <div className="text-[10px] text-destructive mt-1 max-w-[200px] truncate" title={execution.failure_reason}>
                          {execution.failure_reason}
                        </div>
                      )}
                    </TableCell>

                    <TableCell className="text-sm text-muted-foreground">
                      {execution.started_at ? new Date(execution.started_at).toLocaleString() : 'Pending...'}
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
