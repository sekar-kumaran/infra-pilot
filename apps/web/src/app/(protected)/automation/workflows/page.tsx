"use client";

import { useState } from 'react';
import useSWR from 'swr';
import { automationApi } from '@/lib/api/automation';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, PlaySquare, Copy, Settings, Activity } from 'lucide-react';
import { useAuth } from '@/lib/auth';

export default function WorkflowsPage() {
  const { data: workflows, error: workflowsError, isLoading: loadingWorkflows } = useSWR('/automation/playbooks', () => automationApi.getPlaybooks());
  const { data: templates, error: templatesError, isLoading: loadingTemplates } = useSWR('/automation/templates', () => automationApi.getTemplates());
  
  const { hasPermission } = useAuth();
  const [activeTab, setActiveTab] = useState("my-workflows");

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Workflows & Templates</h1>
          <p className="text-muted-foreground mt-1">Manage automated runbooks and discover pre-built templates.</p>
        </div>
        {hasPermission('workflows:create') && (
          <Button className="bg-indigo-600 hover:bg-indigo-700">
            <Plus className="mr-2 h-4 w-4" /> Create Workflow
          </Button>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="my-workflows" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            My Workflows
          </TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center gap-2">
            <PlaySquare className="w-4 h-4" />
            Template Library
            <Badge variant="secondary" className="ml-1 px-1.5 py-0 text-[10px]">New</Badge>
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
              </TableRow>
            </TableHeader>
            <TableBody>
              {loadingWorkflows ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8">
                    <div className="flex justify-center"><Activity className="w-6 h-6 animate-spin text-indigo-500" /></div>
                  </TableCell>
                </TableRow>
              ) : workflowsError ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-rose-500">Failed to load workflows.</TableCell>
                </TableRow>
              ) : workflows?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-12">
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
                  <TableRow key={workflow.id} className="hover:bg-muted/30 cursor-pointer">
                    <TableCell className="font-medium">
                      {workflow.name}
                      <div className="text-xs text-muted-foreground font-normal">{workflow.description || 'No description'}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-[10px]">v{workflow.version}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className="bg-indigo-500/10 text-indigo-600 hover:bg-indigo-500/20 shadow-none border-0">
                        {workflow.trigger_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={workflow.status === 'active' ? 'default' : 'secondary'} className={workflow.status === 'active' ? 'bg-emerald-500 hover:bg-emerald-600' : ''}>
                        {workflow.status || 'Active'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">{new Date(workflow.updated_at).toLocaleDateString()}</TableCell>
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
                    <Button variant="outline" className="w-full group">
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
