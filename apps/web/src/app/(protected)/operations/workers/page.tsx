"use client";

import useSWR from 'swr';
import { operationsApi } from '@/lib/api/operations';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Activity, Server, Zap, RefreshCw, StopCircle, PlayCircle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

export default function WorkersPage() {
    const { data: workers = [], error, isLoading, mutate } = useSWR('/operations/workers', operationsApi.getWorkers, { refreshInterval: 30000 });

    const total = workers.length;
    const online = workers.filter(w => w.status === 'ONLINE').length;
    const degraded = workers.filter(w => w.status === 'DEGRADED').length;
    const offline = workers.filter(w => w.status === 'OFFLINE').length;
    const activeTasks = workers.reduce((acc, w) => acc + w.active_tasks, 0);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-200 to-slate-400 bg-clip-text text-transparent">Worker Fleet Management</h1>
                    <p className="text-slate-400">Monitor and manage execution workers across the infrastructure control plane.</p>
                </div>
                <Button onClick={() => mutate()} disabled={isLoading} variant="outline" className="border-slate-700 bg-slate-900">
                    <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                    Refresh Fleet
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="bg-slate-900/50 border-slate-800 backdrop-blur">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Total Workers</CardTitle>
                        <Server className="h-4 w-4 text-slate-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-slate-100">{total}</div>
                    </CardContent>
                </Card>
                <Card className="bg-slate-900/50 border-slate-800 backdrop-blur">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Online</CardTitle>
                        <Activity className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-emerald-500">{online}</div>
                    </CardContent>
                </Card>
                <Card className="bg-slate-900/50 border-slate-800 backdrop-blur">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Offline / Degraded</CardTitle>
                        <StopCircle className="h-4 w-4 text-rose-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-rose-500">{offline + degraded}</div>
                    </CardContent>
                </Card>
                <Card className="bg-slate-900/50 border-slate-800 backdrop-blur">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Active Tasks</CardTitle>
                        <Zap className="h-4 w-4 text-indigo-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-indigo-400">{activeTasks}</div>
                    </CardContent>
                </Card>
            </div>

            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur">
                <CardHeader>
                    <CardTitle className="text-slate-200">Worker Nodes</CardTitle>
                </CardHeader>
                <CardContent>
                    {workers.length === 0 ? (
                        <div className="py-8 text-center text-slate-500">
                            No worker nodes found in the fleet.
                        </div>
                    ) : (
                        <div className="relative overflow-x-auto">
                            <table className="w-full text-sm text-left text-slate-300">
                                <thead className="text-xs text-slate-400 uppercase bg-slate-900/80">
                                    <tr>
                                        <th className="px-4 py-3">Worker ID</th>
                                        <th className="px-4 py-3">Host</th>
                                        <th className="px-4 py-3">Status</th>
                                        <th className="px-4 py-3">Queue</th>
                                        <th className="px-4 py-3">Active Tasks</th>
                                        <th className="px-4 py-3">Concurrency</th>
                                        <th className="px-4 py-3">Version</th>
                                        <th className="px-4 py-3">Last Heartbeat</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {workers.map((w) => (
                                        <tr key={w.id} className="border-b border-slate-800 bg-slate-900/30 hover:bg-slate-800/50">
                                            <td className="px-4 py-3 font-medium text-slate-200">{w.worker_id}</td>
                                            <td className="px-4 py-3">{w.hostname}</td>
                                            <td className="px-4 py-3">
                                                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${w.status === 'ONLINE' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'}`}>
                                                    {w.status}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 font-mono text-xs">{w.queue || 'celery'}</td>
                                            <td className="px-4 py-3">{w.active_tasks}</td>
                                            <td className="px-4 py-3">{w.concurrency}</td>
                                            <td className="px-4 py-3">{w.version}</td>
                                            <td className="px-4 py-3">{w.last_heartbeat ? new Date(w.last_heartbeat).toLocaleString() : 'N/A'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
