"use client";

import useSWR from 'swr';
import { fetchApi } from '@/lib/api/client';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Shield, ShieldAlert, ShieldCheck, CheckCircle2, XCircle, ChevronRight, FileText, AlertTriangle, RefreshCw } from "lucide-react";
import { Badge } from '@/components/ui/badge';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

export default function CompliancePage() {
  const { data: compliance, error, isLoading } = useSWR('/governance/compliance', () => fetchApi<{ global_score: number; global_passing: number; global_failing: number; frameworks: any[]; findings: any[] }>('/governance/compliance'));


  const frameworks = compliance?.frameworks || [];
  const findings = compliance?.findings || [];
  
  const pieData = compliance ? [
    { name: 'Passing Controls', value: compliance.global_passing || 0, color: '#10b981' },
    { name: 'Failing Controls', value: compliance.global_failing || 0, color: '#f43f5e' }
  ] : [];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Compliance & Governance</h1>
          <p className="text-muted-foreground mt-1">Continuous security scanning against standard frameworks.</p>
        </div>
        <Button className="bg-teal-600 hover:bg-teal-700">
          <FileText className="w-4 h-4 mr-2" /> Generate Report
        </Button>
      </div>

      {isLoading ? (
        <div className="p-12 text-center text-slate-500 flex flex-col items-center">
          <RefreshCw className="w-8 h-8 animate-spin text-teal-500 mb-4" />
          Running compliance scans across providers...
        </div>
      ) : error ? (
        <div className="p-8">
          <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-md">
            <h3 className="font-bold flex items-center gap-2"><AlertTriangle className="w-5 h-5"/> Compliance Scan Failed</h3>
            <p className="font-mono text-sm mt-2">API: /api/v1/governance/compliance</p>
            <p className="text-sm mt-1">Reason: {error.message}</p>
          </div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="shadow-sm md:col-span-1">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg text-slate-700">Global Score</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col items-center justify-center">
                <div className="h-40 w-full relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={70}
                        paddingAngle={5}
                        dataKey="value"
                        stroke="none"
                      >
                        {pieData.map((entry: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <span className="text-2xl font-bold text-teal-600">{compliance?.global_score || 0}%</span>
                  </div>
                </div>
                <div className="flex gap-4 mt-2 text-sm">
                  <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-emerald-500" /> Passing: {compliance?.global_passing || 0}</div>
                  <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-rose-500" /> Failing: {compliance?.global_failing || 0}</div>
                </div>
              </CardContent>
            </Card>

            <div className="md:col-span-3 grid grid-cols-1 sm:grid-cols-2 gap-4">
              {frameworks.length === 0 ? (
                <div className="col-span-2 flex items-center justify-center text-slate-400 p-8 border-2 border-dashed rounded-xl">
                  No compliance frameworks configured.
                </div>
              ) : frameworks.map((fw: any) => (
                <Card key={fw.id} className="shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                  <CardHeader className="pb-2">
                    <div className="flex justify-between items-start">
                      <Badge variant="outline" className="bg-slate-50 text-slate-500">{fw.provider}</Badge>
                      {fw.score >= 90 ? <ShieldCheck className="w-5 h-5 text-emerald-500" /> : <ShieldAlert className="w-5 h-5 text-amber-500" />}
                    </div>
                    <CardTitle className="text-lg mt-2">{fw.name}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-end gap-2 mb-2">
                      <span className={`text-3xl font-bold ${fw.score >= 90 ? 'text-emerald-500' : fw.score >= 80 ? 'text-amber-500' : 'text-rose-500'}`}>
                        {fw.score}%
                      </span>
                      <span className="text-sm text-slate-500 mb-1">compliant</span>
                    </div>
                    <Progress value={fw.score} className={`h-2 mb-4 ${fw.score >= 90 ? '*:bg-emerald-500' : fw.score >= 80 ? '*:bg-amber-500' : '*:bg-rose-500'}`} />
                    <div className="flex justify-between text-xs">
                      <span className="text-emerald-600 font-medium flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> {fw.passing} Passing</span>
                      <span className="text-rose-500 font-medium flex items-center gap-1"><XCircle className="w-3 h-3" /> {fw.failing} Failing</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <Card className="shadow-sm">
            <CardHeader className="border-b bg-slate-50 dark:bg-slate-900/50">
              <CardTitle className="text-lg">Top Failing Controls</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y">
                {findings.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">No failing controls found. Great job!</div>
                ) : findings.map((finding: any) => (
                  <div key={finding.id} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 flex items-center justify-between group cursor-pointer transition-colors">
                    <div className="flex items-start gap-4 flex-1">
                      <div className={`mt-1 p-1.5 rounded-md ${
                        finding.severity === 'Critical' ? 'bg-rose-100 text-rose-600' : 
                        finding.severity === 'High' ? 'bg-orange-100 text-orange-600' : 
                        'bg-amber-100 text-amber-600'
                      }`}>
                        <Shield className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="font-medium text-slate-900 dark:text-slate-100">{finding.rule}</h4>
                        <div className="flex items-center gap-3 mt-1 text-sm text-slate-500">
                          <Badge variant="outline" className="text-[10px] uppercase font-mono">{finding.framework}</Badge>
                          <span>Resource: <span className="font-mono text-slate-600 dark:text-slate-400">{finding.resource}</span></span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge className={`shadow-none border-0 ${
                        finding.severity === 'Critical' ? 'bg-rose-500/10 text-rose-600 hover:bg-rose-500/20' : 
                        finding.severity === 'High' ? 'bg-orange-500/10 text-orange-600 hover:bg-orange-500/20' : 
                        'bg-amber-500/10 text-amber-600 hover:bg-amber-500/20'
                      }`}>
                        {finding.severity}
                      </Badge>
                      <Button variant="ghost" size="icon" className="text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">
                        <ChevronRight className="w-5 h-5" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
