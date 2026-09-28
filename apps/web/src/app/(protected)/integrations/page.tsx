"use client";

import useSWR from 'swr';
import { integrationsApi, IntegrationResponse } from '@/lib/api/integrations';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Plus, RefreshCcw, Play, Square, Settings } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { toast } from 'sonner';
import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export default function IntegrationsPage() {
  const { data: integrations, error, isLoading, mutate } = useSWR('/integrations', () => integrationsApi.list());
  const { hasPermission } = useAuth();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    provider: 'prometheus',
    description: '',
    base_url: '',
    bearer_token: '',
    status_endpoint: '/nagios/cgi-bin/status.dat',
    username: '',
    password: '',
    api_key: '',
    kubeconfig: '',
    aws_access_key_id: '',
    aws_secret_access_key: '',
    aws_region: 'us-east-1',
    inventory_url: '',
    private_key: '',
  });

  const PROVIDERS = [
    { value: 'docker',       label: '🐳 Docker Engine',          category: 'Container' },
    { value: 'kubernetes',   label: '☸️ Kubernetes',             category: 'Container' },
    { value: 'prometheus',   label: '📊 Prometheus',             category: 'Monitoring' },
    { value: 'grafana',      label: '📈 Grafana',                category: 'Monitoring' },
    { value: 'nagios',       label: '🔔 Nagios',                 category: 'Monitoring' },
    { value: 'aws',          label: '☁️ Amazon Web Services',    category: 'Cloud' },
    { value: 'terraform',    label: '🏗️ Terraform Cloud',        category: 'IaC' },
    { value: 'ansible',      label: '🔧 Ansible',               category: 'Automation' },
  ];

  const handleCreate = async () => {
    let configuration: Record<string, string> = {};
    const p = formData.provider;

    if (p === 'prometheus') {
      configuration = { base_url: formData.base_url, ...(formData.bearer_token ? { bearer_token: formData.bearer_token } : {}) };
    } else if (p === 'nagios') {
      configuration = { base_url: formData.base_url, status_endpoint: formData.status_endpoint, username: formData.username, password: formData.password };
    } else if (p === 'docker') {
      configuration = { base_url: formData.base_url || 'http://docker-proxy:2375' };
    } else if (p === 'grafana') {
      configuration = { base_url: formData.base_url, api_key: formData.api_key };
    } else if (p === 'kubernetes') {
      configuration = { kubeconfig: formData.kubeconfig };
    } else if (p === 'aws') {
      configuration = { aws_access_key_id: formData.aws_access_key_id, aws_secret_access_key: formData.aws_secret_access_key, aws_region: formData.aws_region };
    } else if (p === 'terraform') {
      configuration = { base_url: formData.base_url || 'https://app.terraform.io', api_token: formData.bearer_token, ...(formData.aws_access_key_id ? { organization: formData.aws_access_key_id } : {}) };
    } else if (p === 'ansible') {
      configuration = { inventory_url: formData.inventory_url, username: formData.username, ...(formData.private_key ? { private_key: formData.private_key } : {}) };
    } else if (p === 'test_provider') {
      configuration = { test_mode: 'true' };
    }

    try {
      await integrationsApi.create({ name: formData.name, provider: formData.provider, description: formData.description, configuration });
      toast.success('Integration created successfully');
      setIsDialogOpen(false);
      setFormData({ name: '', provider: 'prometheus', description: '', base_url: '', bearer_token: '', status_endpoint: '/nagios/cgi-bin/status.dat', username: '', password: '', api_key: '', kubeconfig: '', aws_access_key_id: '', aws_secret_access_key: '', aws_region: 'us-east-1', inventory_url: '', private_key: '' });
      mutate();
    } catch (err: any) {
      toast.error(`Failed to create integration: ${err.message}`);
    }
  };

  const handleToggle = async (integration: IntegrationResponse) => {
    try {
      if (integration.status !== 'DISABLED') {
        await integrationsApi.disable(integration.id);
        toast.success(`${integration.name} disabled`);
      } else {
        await integrationsApi.enable(integration.id);
        toast.success(`${integration.name} enabled`);
      }
      mutate();
    } catch (err: any) {
      toast.error(`Failed to toggle: ${err.message}`);
    }
  };

  const handleDiscover = async (id: string) => {
    try {
      const res = await integrationsApi.discover(id);
      toast.info(`Discovery Job Started: ${res.job_id}`);
    } catch (err: any) {
      toast.error(`Discovery failed: ${err.message}`);
    }
  };

  const handleValidate = async (id: string) => {
    try {
      await integrationsApi.validate(id);
      toast.info(`Validation Job Queued`);
      mutate();
    } catch (err: any) {
      toast.error(`Validation failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Integrations</h1>
        {hasPermission('integrations:create') && (
          <>
            <Button onClick={() => setIsDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" /> Add Integration
            </Button>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Add Integration</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Name</Label>
                  <Input value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} placeholder="Production Docker" />
                </div>
                <div className="space-y-2">
                  <Label>Provider</Label>
                  <Select value={formData.provider} onValueChange={(v) => setFormData({...formData, provider: v || ''})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select Provider" />
                    </SelectTrigger>
                    <SelectContent>
                      {PROVIDERS.map(p => (
                        <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Input value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} placeholder="Optional description" />
                </div>
                
                {/* Docker */}
                {formData.provider === 'docker' && (
                  <div className="space-y-2">
                    <Label>Docker API URL</Label>
                    <Input value={formData.base_url} onChange={e => setFormData({...formData, base_url: e.target.value})} placeholder="http://docker-proxy:2375" />
                    <p className="text-xs text-muted-foreground">Use the docker-proxy service URL if running inside Docker</p>
                  </div>
                )}

                {/* Prometheus */}
                {formData.provider === 'prometheus' && (
                  <>
                    <div className="space-y-2">
                      <Label>Base URL</Label>
                      <Input value={formData.base_url} onChange={e => setFormData({...formData, base_url: e.target.value})} placeholder="http://prometheus:9090" />
                    </div>
                    <div className="space-y-2">
                      <Label>Bearer Token (Optional)</Label>
                      <Input type="password" value={formData.bearer_token} onChange={e => setFormData({...formData, bearer_token: e.target.value})} placeholder="••••••••" />
                    </div>
                  </>
                )}

                {/* Grafana */}
                {formData.provider === 'grafana' && (
                  <>
                    <div className="space-y-2">
                      <Label>Grafana URL</Label>
                      <Input value={formData.base_url} onChange={e => setFormData({...formData, base_url: e.target.value})} placeholder="http://grafana:3000" />
                    </div>
                    <div className="space-y-2">
                      <Label>API Key (Service Account Token)</Label>
                      <Input type="password" value={formData.api_key} onChange={e => setFormData({...formData, api_key: e.target.value})} placeholder="glsa_••••••••" />
                    </div>
                  </>
                )}

                {/* Nagios */}
                {formData.provider === 'nagios' && (
                  <>
                    <div className="space-y-2">
                      <Label>Base URL</Label>
                      <Input value={formData.base_url} onChange={e => setFormData({...formData, base_url: e.target.value})} placeholder="http://nagios.company.com" />
                    </div>
                    <div className="space-y-2">
                      <Label>Status CGI Endpoint</Label>
                      <Input value={formData.status_endpoint} onChange={e => setFormData({...formData, status_endpoint: e.target.value})} placeholder="/nagios/cgi-bin/status.dat" />
                    </div>
                    <div className="space-y-2">
                      <Label>Username</Label>
                      <Input value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} placeholder="nagiosadmin" />
                    </div>
                    <div className="space-y-2">
                      <Label>Password</Label>
                      <Input type="password" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} placeholder="••••••••" />
                    </div>
                  </>
                )}

                {/* Kubernetes */}
                {formData.provider === 'kubernetes' && (
                  <div className="space-y-2">
                    <Label>Kubeconfig (Base64 encoded)</Label>
                    <textarea
                      className="w-full h-28 text-xs font-mono p-2 border rounded-md bg-background resize-none"
                      value={formData.kubeconfig}
                      onChange={e => setFormData({...formData, kubeconfig: e.target.value})}
                      placeholder="Paste base64-encoded kubeconfig here..."
                    />
                    <p className="text-xs text-muted-foreground">Run: <code className="bg-muted px-1 rounded">base64 -w 0 ~/.kube/config</code></p>
                  </div>
                )}

                {/* AWS */}
                {formData.provider === 'aws' && (
                  <>
                    <div className="space-y-2">
                      <Label>AWS Access Key ID</Label>
                      <Input value={formData.aws_access_key_id} onChange={e => setFormData({...formData, aws_access_key_id: e.target.value})} placeholder="AKIAIOSFODNN7EXAMPLE" />
                    </div>
                    <div className="space-y-2">
                      <Label>AWS Secret Access Key</Label>
                      <Input type="password" value={formData.aws_secret_access_key} onChange={e => setFormData({...formData, aws_secret_access_key: e.target.value})} placeholder="••••••••" />
                    </div>
                    <div className="space-y-2">
                      <Label>Default Region</Label>
                      <Input value={formData.aws_region} onChange={e => setFormData({...formData, aws_region: e.target.value})} placeholder="us-east-1" />
                    </div>
                  </>
                )}

                {/* Terraform */}
                {formData.provider === 'terraform' && (
                  <>
                    <div className="space-y-2">
                      <Label>Terraform Cloud URL</Label>
                      <Input value={formData.base_url} onChange={e => setFormData({...formData, base_url: e.target.value})} placeholder="https://app.terraform.io" />
                      <p className="text-xs text-muted-foreground">Leave default for Terraform Cloud. Change for Terraform Enterprise.</p>
                    </div>
                    <div className="space-y-2">
                      <Label>Organization (Optional)</Label>
                      <Input value={formData.aws_access_key_id} onChange={e => setFormData({...formData, aws_access_key_id: e.target.value})} placeholder="my-org-name" />
                      <p className="text-xs text-muted-foreground">Leave blank to discover all accessible organizations.</p>
                    </div>
                    <div className="space-y-2">
                      <Label>API Token</Label>
                      <Input type="password" value={formData.bearer_token} onChange={e => setFormData({...formData, bearer_token: e.target.value})} placeholder="••••••••" />
                      <p className="text-xs text-muted-foreground">Generate at: Settings → Tokens → User API Tokens</p>
                    </div>
                  </>
                )}

                {/* Ansible */}
                {formData.provider === 'ansible' && (
                  <>
                    <div className="space-y-2">
                      <Label>Ansible Controller / AWX URL</Label>
                      <Input value={formData.inventory_url} onChange={e => setFormData({...formData, inventory_url: e.target.value})} placeholder="http://ansible-controller:8080" />
                    </div>
                    <div className="space-y-2">
                      <Label>Username</Label>
                      <Input value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} placeholder="admin" />
                    </div>
                    <div className="space-y-2">
                      <Label>Password / API Token</Label>
                      <Input type="password" value={formData.private_key} onChange={e => setFormData({...formData, private_key: e.target.value})} placeholder="••••••••" />
                    </div>
                  </>
                )}

              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                <Button onClick={handleCreate} disabled={!formData.name}>Create Integration</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          </>
        )}
      </div>

      <div className="border rounded-md bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Provider</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Capabilities</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8">Loading integrations...</TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-red-500">Failed to load integrations.</TableCell>
              </TableRow>
            ) : integrations?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-slate-500 py-8">No integrations found.</TableCell>
              </TableRow>
            ) : (
              integrations?.map((integration) => (
                <TableRow key={integration.id}>
                  <TableCell className="font-medium">{integration.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{integration.provider}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={integration.status === 'healthy' ? 'default' : (integration.status === 'error' ? 'destructive' : 'secondary')}>
                      {integration.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      <Badge variant="secondary" className="text-xs">{integration.circuit_state}</Badge>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end space-x-2">
                      {hasPermission('integrations:update') && (
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleToggle(integration)}
                        >
                          {integration.status !== 'DISABLED' ? <Square className="h-4 w-4 text-red-500" /> : <Play className="h-4 w-4 text-green-500" />}
                        </Button>
                      )}
                      {hasPermission('integrations:validate') && (
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleValidate(integration.id)}
                          title="Validate Connection"
                        >
                          <Settings className="h-4 w-4" />
                        </Button>
                      )}
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => handleDiscover(integration.id)}
                        title="Run Discovery"
                      >
                        <RefreshCcw className="h-4 w-4" />
                      </Button>
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
