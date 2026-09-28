"use client";

import { useState } from 'react';
import { policiesApi, PolicySimulationRequest, PolicySimulationResponse } from '@/lib/api/policies';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertCircle, CheckCircle2, ShieldAlert, Zap } from 'lucide-react';

export default function PolicySimulatorPage() {
  const [request, setRequest] = useState<PolicySimulationRequest>({
    provider: 'kubernetes',
    resource_type: 'KUBERNETES_DEPLOYMENT',
    action: 'kubernetes_restart_deployment',
    risk: 'HIGH',
    severity: 'CRITICAL',
    environment: 'production'
  });
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PolicySimulationResponse | null>(null);

  const handleSimulate = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await policiesApi.simulate(request);
      setResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-200 to-slate-400 bg-clip-text text-transparent">Policy Simulator</h1>
          <p className="text-slate-400">Dry-run infrastructure operations against active governance policies.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-slate-800 bg-slate-900/50 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-slate-200 flex items-center gap-2">
              <Zap className="h-5 w-5 text-indigo-400" />
              Operation Context
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Provider</Label>
                <Input 
                  value={request.provider} 
                  onChange={(e) => setRequest({...request, provider: e.target.value})} 
                  className="bg-slate-950 border-slate-800"
                />
              </div>
              <div className="space-y-2">
                <Label>Action</Label>
                <Input 
                  value={request.action} 
                  onChange={(e) => setRequest({...request, action: e.target.value})} 
                  className="bg-slate-950 border-slate-800"
                />
              </div>
              <div className="space-y-2">
                <Label>Resource Type</Label>
                <Input 
                  value={request.resource_type} 
                  onChange={(e) => setRequest({...request, resource_type: e.target.value})} 
                  className="bg-slate-950 border-slate-800"
                />
              </div>
              <div className="space-y-2">
                <Label>Risk Level</Label>
                <Select value={request.risk} onValueChange={(val) => setRequest({...request, risk: val || undefined})}>
                  <SelectTrigger className="bg-slate-950 border-slate-800">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LOW">LOW</SelectItem>
                    <SelectItem value="MEDIUM">MEDIUM</SelectItem>
                    <SelectItem value="HIGH">HIGH</SelectItem>
                    <SelectItem value="CRITICAL">CRITICAL</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Incident Severity</Label>
                <Select value={request.severity} onValueChange={(val) => setRequest({...request, severity: val || undefined})}>
                  <SelectTrigger className="bg-slate-950 border-slate-800">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LOW">LOW</SelectItem>
                    <SelectItem value="MEDIUM">MEDIUM</SelectItem>
                    <SelectItem value="HIGH">HIGH</SelectItem>
                    <SelectItem value="CRITICAL">CRITICAL</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Environment</Label>
                <Input 
                  value={request.environment} 
                  onChange={(e) => setRequest({...request, environment: e.target.value})} 
                  className="bg-slate-950 border-slate-800"
                />
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button onClick={handleSimulate} disabled={loading} className="w-full bg-indigo-600 hover:bg-indigo-700">
              {loading ? "Simulating..." : "Evaluate Policy"}
            </Button>
          </CardFooter>
        </Card>

        <div>
          {result ? (
            <Card className="border-slate-800 bg-slate-900/50 backdrop-blur h-full">
              <CardHeader>
                <CardTitle className="text-slate-200">Evaluation Result</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-center py-6">
                  {result.decision === 'DENY' && (
                    <div className="text-center space-y-2">
                      <ShieldAlert className="h-16 w-16 text-rose-500 mx-auto" />
                      <h2 className="text-2xl font-bold text-rose-500">DENIED</h2>
                    </div>
                  )}
                  {result.decision === 'WAITING_APPROVAL' && (
                    <div className="text-center space-y-2">
                      <AlertCircle className="h-16 w-16 text-amber-500 mx-auto" />
                      <h2 className="text-2xl font-bold text-amber-500">REQUIRES APPROVAL</h2>
                    </div>
                  )}
                  {result.decision === 'ALLOW' && (
                    <div className="text-center space-y-2">
                      <CheckCircle2 className="h-16 w-16 text-emerald-500 mx-auto" />
                      <h2 className="text-2xl font-bold text-emerald-500">ALLOWED</h2>
                    </div>
                  )}
                </div>

                <div className="space-y-2 text-sm text-slate-300 bg-slate-950 p-4 rounded-md border border-slate-800">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Reason:</span>
                    <span className="font-medium">{result.reason}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Matched Policies:</span>
                    <span className="font-medium">{result.matched_policies.join(', ') || 'None'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Risk Assessment:</span>
                    <span className="font-medium">{result.risk}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="h-full border border-dashed border-slate-800 rounded-lg flex items-center justify-center text-slate-500 bg-slate-900/30">
              Run a simulation to see the policy decision.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
