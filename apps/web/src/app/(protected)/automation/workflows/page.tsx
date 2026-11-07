"use client";

import { useState } from 'react';
import useSWR from 'swr';
import { automationApi } from '@/lib/api/automation';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, PlaySquare, Copy, Settings, Activity, Play } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { toast } from 'sonner';

export default function WorkflowsPage() {
  const { data: workflows, error: workflowsError, isLoading: loadingWorkflows, mutate } = useSWR('/automation/playbooks', () => automationApi.getPlaybooks());
  const { data: templates, isLoading: loadingTemplates } = useSWR('/automation/templates', () => automationApi.getTemplates());
  
  const { hasPermission } = useAuth();
  const [activeTab, setActiveTab] = useState("my-workflows");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', trigger_type: 'MANUAL', action_name: 'restart_service' });

  const handleCreate = async () => {
    try {
      await automationApi.createPlaybook({
        name: form.name,
        description: form.description,
        trigger_type: form.trigger_type,
        steps: [{ name: `${form.name} Step 1`, action_name: form.action_name, risk_level: 'LOW' }],
      });
      toast.success(`Workflow "${form.name}" created`);
      setIsCreateOpen(false);
      setForm({ name: '', description: '', trigger_type: 'MANUAL', action_name: 'restart_service' });
      mutate();
    } catch (err: any) {
      toast.error(`Failed to create workflow: ${err.message}`);
    }
  };

  const handleCloneTemplate = async (tpl: any) => {
    try {
      await automationApi.createPlaybook({
        name: `${tpl.name} (${Math.floor(Math.random() * 900 + 100)})`,
        description: tpl.description,
        trigger_type: tpl.trigger_type || 'MANUAL',
        steps: [{ name: tpl.name, action_name: 'test_action_success', risk_level: 'LOW' }],
      });
      toast.success(`Cloned template "${tpl.name}" to your workflows`);
      mutate();
      setActiveTab("my-workflows");
    } catch (err: any) {
      toast.error(`Failed to clone template: ${err.message}`);
    }
  };

  const handleRunPlaybook = async (wf: any) => {
    try {
      const res = await automationApi.triggerExecution({ playbook_id: wf.id });
      toast.success(`Triggered "${wf.name}" (Status: ${res.status})`);
    } catch (err: any) {
      toast.error(`Execution failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Workflows & Runbook Templates</h1>
          <p className="text-muted-foreground mt-1">Manage automated runbooks, execute remediations, and clone pre-built templates.</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} className="bg-indigo-600 hover:bg-indigo-700">
          <Plus className="mr-2 h-4 w-4" /> Create Workflow
        </Button>
      </div>

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Automated Runbook Workflow</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-3">
            <div className="space-y-2">
              <Label>Workflow Name</Label>
              <Input value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="e.g. Restart NexusPay Worker Pool" />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Input value={form.description} onChange={e => setForm({...form, description: e.target.value})} placeholder="Automated recovery with post-execution verification" />
            </div>
            <div className="space-y-2">
              <Label>Primary Action</Label>
              <Input value={form.action_name} onChange={e => setForm({...form, action_name: e.target.value})} placeholder="restart_service" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={!form.name} className="bg-indigo-600 hover:bg-indigo-700">Create Workflow</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="my-workflows" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            My Workflows
          </TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center gap-2">
            <PlaySquare className="w-4 h-4" />
            Template Library
            <Badge variant="secondary" className="ml-1 px-1.5 py-0 text-[10px]">Ready</Badge>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="my-workflows" className="border rounded-xl bg-card shadow-sm overflow-hidden">
          <Table>
            <TableHeader className="bg-muted/50">
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Trigger Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Updated At</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loadingWorkflows ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    <div className="flex justify-center"><Activity className="w-6 h-6 animate-spin text-indigo-500" /></div>
                  </TableCell>
                </TableRow>
              ) : workflowsError ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-rose-500">Failed to load workflows.</TableCell>
                </TableRow>
              ) : workflows?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground py-12">
                    <div className="flex flex-col items-center">
                      <Settings className="w-12 h-12 opacity-20 mb-3" />
                      <p>No active workflows found.</p>
                      <Button variant="link" onClick={() => setActiveTab("templates")} className="mt-2">
                        Browse Templates
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                workflows?.map((workflow) => (
                  <TableRow key={workflow.id} className="hover:bg-muted/30">
                    <TableCell className="font-medium">
                      {workflow.name}
                      <div className="text-xs text-muted-foreground font-normal">{workflow.description || 'Automated runbook'}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-[10px]">v{workflow.version || 1}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className="bg-indigo-500/10 text-indigo-600 shadow-none border-0">
                        {workflow.trigger_type || 'MANUAL'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className="bg-emerald-500 text-white">
                        {workflow.status || 'ACTIVE'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {workflow.updated_at ? new Date(workflow.updated_at).toLocaleDateString() : 'Today'}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button size="sm" onClick={() => handleRunPlaybook(workflow)} className="bg-indigo-600 hover:bg-indigo-700">
                        <Play className="w-3.5 h-3.5 mr-1" /> Execute
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="templates" className="mt-4">
          {loadingTemplates ? (
            <div className="flex justify-center py-12"><Activity className="w-8 h-8 animate-spin text-indigo-500" /></div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {templates?.map((tpl) => (
                <Card key={tpl.id} className="hover:shadow-md transition-all border-dashed border-2 hover:border-indigo-300">
                  <CardHeader className="pb-3">
                    <div className="flex justify-between items-start mb-2">
                      <div className="p-2 bg-indigo-50 dark:bg-indigo-950/30 rounded-lg text-indigo-600 dark:text-indigo-400">
                        <PlaySquare className="w-5 h-5" />
                      </div>
                      <Badge variant="secondary" className="font-mono text-[10px] uppercase">
                        {tpl.trigger_type}
                      </Badge>
                    </div>
                    <CardTitle className="text-lg">{tpl.name}</CardTitle>
                    <CardDescription className="line-clamp-2">{tpl.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2 mb-4">
                      {tpl.tags?.map((tag: string) => (
                        <span key={tag} className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded text-[10px] font-medium uppercase tracking-wider">
                          {tag}
                        </span>
                      ))}
                    </div>
                    <Button variant="outline" className="w-full group" onClick={() => handleCloneTemplate(tpl)}>
                      <Copy className="w-4 h-4 mr-2 text-muted-foreground group-hover:text-foreground transition-colors" />
                      Clone Template
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
