"use client";

import useSWR from 'swr';
import { fetchApi } from '@/lib/api/client';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from "@/components/ui/badge";
import { Clock, Plus, Play, Pause, MoreVertical, Calendar, AlertTriangle, RefreshCw } from "lucide-react";

export default function SchedulerPage() {
  const { data: schedulesData, error, isLoading } = useSWR('/automation/schedules', () => fetchApi<{ items: any[]; stats: any }>('/automation/schedules'));
  
  const schedules = schedulesData?.items || [];
  const stats = schedulesData?.stats || { active: 0, today: 0, success_rate: 0 };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Automation Scheduler</h1>
          <p className="text-muted-foreground mt-1">Manage cron jobs and scheduled runbook executions.</p>
        </div>
        <Button className="bg-indigo-600 hover:bg-indigo-700">
          <Plus className="w-4 h-4 mr-2" /> New Schedule
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Schedules</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? <RefreshCw className="w-4 h-4 animate-spin text-slate-400" /> : <div className="text-2xl font-bold">{stats.active}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Executions Today</CardTitle>
            <Play className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? <RefreshCw className="w-4 h-4 animate-spin text-slate-400" /> : <div className="text-2xl font-bold">{stats.today}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? <RefreshCw className="w-4 h-4 animate-spin text-slate-400" /> : <div className="text-2xl font-bold text-emerald-500">{stats.success_rate}%</div>}
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-sm">
        {error ? (
          <div className="p-8">
            <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-md">
              <h3 className="font-bold flex items-center gap-2"><AlertTriangle className="w-5 h-5"/> Failed to load schedules</h3>
              <p className="font-mono text-sm mt-2">API: /api/v1/automation/schedules</p>
              <p className="text-sm mt-1">Reason: {error.message}</p>
            </div>
          </div>
        ) : isLoading ? (
          <div className="p-12 text-center text-slate-500 flex flex-col items-center">
            <RefreshCw className="w-8 h-8 animate-spin text-indigo-500 mb-4" />
            Loading schedules...
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-slate-50 dark:bg-slate-900/50">
              <TableRow>
                <TableHead>Schedule Name</TableHead>
                <TableHead>Target Playbook</TableHead>
                <TableHead>Cron Expression</TableHead>
                <TableHead>Next Run</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {schedules.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-slate-500">No schedules configured.</TableCell>
                </TableRow>
              ) : schedules.map((schedule: any) => (
                <TableRow key={schedule.id}>
                  <TableCell className="font-medium">{schedule.name}</TableCell>
                  <TableCell className="text-indigo-600 dark:text-indigo-400">{schedule.playbook}</TableCell>
                  <TableCell><Badge variant="outline" className="font-mono bg-slate-100 dark:bg-slate-800">{schedule.cron}</Badge></TableCell>
                  <TableCell className="text-slate-500 text-sm">{schedule.nextRun}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {schedule.status === 'active' ? (
                        <Badge className="bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20 shadow-none border-0">Active</Badge>
                      ) : (
                        <Badge className="bg-amber-500/10 text-amber-600 hover:bg-amber-500/20 shadow-none border-0">Paused</Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      {schedule.status === 'active' ? (
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-amber-500"><Pause className="w-4 h-4" /></Button>
                      ) : (
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-emerald-500"><Play className="w-4 h-4" /></Button>
                      )}
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400"><MoreVertical className="w-4 h-4" /></Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
