"use client";

import useSWR from 'swr';
import { metricsApi } from '@/lib/api/metrics';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Activity, AlertTriangle, PlaySquare, CheckCircle, XCircle } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function DashboardPage() {
  const { data: metrics, error, isLoading } = useSWR('/system/metrics', metricsApi.getSummary, { refreshInterval: 30000 });

  if (isLoading) return <div className="p-8 animate-pulse flex justify-center text-slate-500">Loading dashboard metrics...</div>;
  if (error) return (
    <div className="p-8">
      <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-md">
        <h3 className="font-bold">Unable to load metrics</h3>
        <p className="font-mono text-sm mt-1">API: /api/v1/system/metrics</p>
        <p className="text-sm mt-1">Reason: {error.message}</p>
        <Button variant="outline" className="mt-4" onClick={() => window.location.reload()}>Retry</Button>
      </div>
    </div>
  );
  if (!metrics) return null;

  const statCards = [
    { title: 'Open Incidents', value: metrics.open_incidents, icon: AlertTriangle, color: 'text-orange-500' },
    { title: 'Critical Incidents', value: metrics.critical_incidents, icon: AlertTriangle, color: 'text-red-500' },
    { title: 'Active Alerts', value: metrics.active_alerts, icon: BellRing, color: 'text-yellow-500' },
    { title: 'Events Processed', value: metrics.events_processed, icon: Activity, color: 'text-blue-500' },
    { title: 'Failed Events', value: metrics.failed_events, icon: XCircle, color: 'text-red-500' },
    { title: 'Automation Executions', value: metrics.automation_executions, icon: PlaySquare, color: 'text-indigo-500' },
    { title: 'Failed Executions', value: metrics.failed_executions, icon: XCircle, color: 'text-red-500' },
    { title: 'Active Integrations', value: metrics.active_integrations, icon: CheckCircle, color: 'text-green-500' },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <h1 className="text-3xl font-bold tracking-tight">Dashboard Overview</h1>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat, index) => (
          <Card key={index} className="shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                {stat.title}
              </CardTitle>
              <stat.icon className={`h-5 w-5 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function BellRing(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
      <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
      <path d="M4 2C2.8 3.7 2 5.7 2 8" />
      <path d="M22 8c0-2.3-.8-4.3-2-6" />
    </svg>
  );
}
