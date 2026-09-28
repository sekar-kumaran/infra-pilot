"use client";

import useSWR from 'swr';
import { fetchApi } from '@/lib/api/client';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Bell, Plus, Mail, MessageSquare, AlertTriangle, Settings2, RefreshCw } from "lucide-react";

export default function NotificationsPage() {
  const { data: notificationsData, error, isLoading } = useSWR('/settings/notifications', () => fetchApi<{ items: any[] }>('/settings/notifications'));
  const channels = notificationsData?.items || [];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Notification Channels</h1>
          <p className="text-muted-foreground mt-1">Configure how and when you receive alerts from InfraPilot.</p>
        </div>
        <Button className="bg-indigo-600 hover:bg-indigo-700">
          <Plus className="w-4 h-4 mr-2" /> Add Channel
        </Button>
      </div>

      {isLoading ? (
        <div className="p-12 text-center text-slate-500 flex flex-col items-center">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-500 mb-4" />
          Loading notification configurations...
        </div>
      ) : error ? (
        <div className="p-8">
          <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-md">
            <h3 className="font-bold flex items-center gap-2"><AlertTriangle className="w-5 h-5"/> Failed to load configurations</h3>
            <p className="font-mono text-sm mt-2">API: /api/v1/settings/notifications</p>
            <p className="text-sm mt-1">Reason: {error.message}</p>
          </div>
        </div>
      ) : channels.length === 0 ? (
        <div className="p-12 text-center text-slate-500 border-2 border-dashed rounded-xl">
          <Bell className="w-12 h-12 mx-auto mb-4 opacity-50 text-indigo-500" />
          <h3 className="text-lg font-medium text-slate-900 mb-1">No channels configured</h3>
          <p>Add a Slack channel, PagerDuty integration, or Email address to start receiving alerts.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {channels.map((channel: any) => (
            <Card key={channel.id} className={`shadow-sm ${channel.status === 'disabled' ? 'opacity-70' : ''}`}>
              <CardHeader className="pb-3 flex flex-row items-start justify-between space-y-0">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    channel.type === 'slack' ? 'bg-blue-100 text-blue-600' :
                    channel.type === 'pagerduty' ? 'bg-emerald-100 text-emerald-600' :
                    'bg-orange-100 text-orange-600'
                  }`}>
                    {channel.type === 'slack' ? <MessageSquare className="w-5 h-5" /> : 
                     channel.type === 'pagerduty' ? <AlertTriangle className="w-5 h-5" /> : 
                     <Mail className="w-5 h-5" />}
                  </div>
                  <div>
                    <CardTitle className="text-base">{channel.name}</CardTitle>
                    <div className="text-xs text-slate-500 font-mono mt-0.5">{channel.target}</div>
                  </div>
                </div>
                <div className={`w-11 h-6 rounded-full flex items-center px-1 ${channel.status === 'active' ? 'bg-indigo-600 justify-end' : 'bg-slate-200 justify-start'}`}>
                  <div className="w-4 h-4 bg-white rounded-full shadow-sm" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  <Badge variant="outline" className="text-[10px] bg-slate-50">Critical Alerts</Badge>
                  {channel.type === 'slack' && <Badge variant="outline" className="text-[10px] bg-slate-50">High Alerts</Badge>}
                </div>
                <div className="mt-4 pt-4 border-t flex justify-end gap-2">
                  <Button variant="ghost" size="sm" className="h-8 text-slate-500">Test</Button>
                  <Button variant="ghost" size="sm" className="h-8 text-slate-500"><Settings2 className="w-4 h-4 mr-1" /> Configure</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
