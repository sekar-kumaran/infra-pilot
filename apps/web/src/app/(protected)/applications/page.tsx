"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import useSWR from 'swr';
import { applicationsApi } from '@/lib/api/applications';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Plus, Search, Box, Activity, AlertTriangle, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';

export default function ApplicationsPage() {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '' });

  const { data: applications, error, isLoading, mutate } = useSWR('/applications', () => applicationsApi.list());

  const handleCreate = async () => {
    try {
      await applicationsApi.create(formData);
      toast.success('Application created successfully');
      setIsDialogOpen(false);
      setFormData({ name: '', description: '' });
      mutate();
    } catch (err: any) {
      toast.error(err.message || 'Failed to create application');
    }
  };

  const filteredApps = applications?.filter(app => 
    app.name.toLowerCase().includes(search.toLowerCase()) || 
    (app.description || '').toLowerCase().includes(search.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'HEALTHY': return 'bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20';
      case 'DEGRADED': return 'bg-amber-500/10 text-amber-500 hover:bg-amber-500/20';
      case 'CRITICAL': return 'bg-rose-500/10 text-rose-500 hover:bg-rose-500/20';
      default: return 'bg-slate-500/10 text-slate-500 hover:bg-slate-500/20';
    }
  };

  if (isLoading) return <div className="flex items-center justify-center h-96"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Applications</h1>
          <p className="text-muted-foreground mt-1">Manage your grouped infrastructure resources and services.</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger render={<Button className="bg-indigo-600 hover:bg-indigo-700" />}>
            <Plus className="w-4 h-4 mr-2" />
            Register Application
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Register New Application</DialogTitle>
              <DialogDescription>
                Create a logical grouping for your infrastructure resources (e.g. "Weather App").
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Application Name</Label>
                <Input 
                  placeholder="e.g. Payment Gateway" 
                  value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Input 
                  placeholder="Brief description of this application..."
                  value={formData.description}
                  onChange={e => setFormData({...formData, description: e.target.value})}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={!formData.name} className="bg-indigo-600 hover:bg-indigo-700">
                Register
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex items-center space-x-2 w-full md:w-1/3 relative">
        <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
        <Input 
          placeholder="Search applications..." 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9 h-10 bg-card/50"
        />
      </div>

      {error ? (
        <div className="bg-destructive/10 text-destructive p-4 rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          <p>Failed to load applications. Ensure the backend is running.</p>
        </div>
      ) : filteredApps?.length === 0 ? (
        <div className="text-center py-20 bg-card/30 rounded-xl border border-dashed border-border">
          <Box className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-medium text-foreground">No applications found</h3>
          <p className="text-sm text-muted-foreground mt-1 mb-4">You haven't registered any applications yet.</p>
          <Button variant="outline" onClick={() => setIsDialogOpen(true)}>
            Register your first application
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredApps?.map(app => (
            <Card 
              key={app.id} 
              className="hover:shadow-md transition-shadow cursor-pointer group"
              onClick={() => router.push(`/applications/${app.id}`)}
            >
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 bg-indigo-500/10 text-indigo-600 rounded-xl group-hover:bg-indigo-500/20 transition-colors">
                      <Box className="w-5 h-5" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{app.name}</CardTitle>
                      <CardDescription className="line-clamp-1 mt-0.5">{app.description || 'No description'}</CardDescription>
                    </div>
                  </div>
                  <Badge className={getStatusColor(app.status)} variant="outline">
                    {app.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="pb-4">
                <div className="grid grid-cols-2 gap-4 mt-2">
                  <div className="flex flex-col bg-slate-50/50 dark:bg-slate-900/50 p-3 rounded-lg border border-border/50">
                    <span className="text-xs text-muted-foreground font-medium mb-1 flex items-center gap-1.5">
                      <Activity className="w-3.5 h-3.5" />
                      Resources
                    </span>
                    <span className="text-2xl font-semibold text-foreground">
                      {app.resource_count}
                    </span>
                  </div>
                  <div className="flex flex-col bg-rose-50/50 dark:bg-rose-950/20 p-3 rounded-lg border border-rose-100 dark:border-rose-900/30">
                    <span className="text-xs text-rose-600/70 dark:text-rose-400/70 font-medium mb-1 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      Incidents
                    </span>
                    <span className="text-2xl font-semibold text-rose-600 dark:text-rose-400">
                      {app.incidents_count}
                    </span>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="pt-0 pb-4 border-t border-border/50 mt-4 flex justify-between items-center">
                <span className="text-xs text-muted-foreground">
                  Updated {new Date(app.updated_at).toLocaleDateString()}
                </span>
                <span className="text-xs font-medium text-indigo-600 flex items-center group-hover:translate-x-1 transition-transform">
                  View Dashboard <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                </span>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
