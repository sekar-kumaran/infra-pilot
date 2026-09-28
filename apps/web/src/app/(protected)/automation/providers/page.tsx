"use client";

import { useEffect, useState } from 'react';
import { fetchApi } from '@/lib/api/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Server, CheckCircle, XCircle, Activity, Box, Shield, Play } from 'lucide-react';

interface ProviderCapability {
  provider: string;
  display_name: string;
  version: string;
  status: string;
  capabilities: string[];
  resources: string[];
  read_operations: string[];
  mutation_operations: string[];
  authentication_requirements: string[];
}

export default function ProvidersPage() {
  const [providers, setProviders] = useState<ProviderCapability[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const capabilities = await fetchApi<ProviderCapability[]>('/providers/capabilities');
        setProviders(capabilities);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch provider capabilities');
      } finally {
        setLoading(false);
      }
    };
    fetchProviders();
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-600">
            Control Plane Providers
          </h1>
          <p className="text-muted-foreground mt-2 text-lg">
            Dynamically discovered integrations powering your autonomous operations.
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex items-center gap-2">
          <Badge variant="outline" className="px-4 py-1.5 text-sm bg-background/50 backdrop-blur-sm border-indigo-200">
            {providers.length} Connected
          </Badge>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive border border-destructive/20 p-4 rounded-xl flex items-center gap-3">
          <XCircle className="h-5 w-5" />
          <p>{error}</p>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="animate-pulse bg-muted/20 border-muted/30 h-64" />
          ))
        ) : (
          providers.map((provider) => (
            <Card 
              key={provider.provider} 
              className="overflow-hidden transition-all duration-300 hover:shadow-xl hover:shadow-indigo-500/10 hover:-translate-y-1 border-muted/40 bg-card/40 backdrop-blur-md"
            >
              <CardHeader className="pb-4 border-b border-border/50 bg-muted/10">
                <div className="flex justify-between items-start">
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 text-indigo-600 dark:text-indigo-400">
                      <Server className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle className="capitalize text-xl font-bold">{provider.display_name}</CardTitle>
                      <CardDescription className="flex items-center gap-2 mt-1">
                        <span className="text-xs uppercase tracking-wider font-semibold opacity-70">
                          v{provider.version || "1.0"}
                        </span>
                      </CardDescription>
                    </div>
                  </div>
                  <Badge 
                    variant={provider.status === "healthy" ? "default" : "destructive"}
                    className={`shadow-sm ${provider.status === 'healthy' ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-500/25 border-none' : ''}`}
                  >
                    {provider.status === "healthy" ? (
                      <span className="flex items-center gap-1.5"><CheckCircle className="w-3 h-3"/> HEALTHY</span>
                    ) : (
                      <span className="flex items-center gap-1.5"><XCircle className="w-3 h-3"/> {provider.status.toUpperCase()}</span>
                    )}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="pt-5 space-y-5">
                
                {/* Capabilities */}
                {provider.capabilities && provider.capabilities.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                      <Shield className="w-4 h-4" /> Capabilities
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {provider.capabilities.map(cap => (
                        <Badge key={cap} variant="secondary" className="bg-secondary/50 font-medium">{cap}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Resources */}
                {provider.resources && provider.resources.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                      <Box className="w-4 h-4" /> Resources
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {provider.resources.map(res => (
                        <Badge key={res} variant="outline" className="border-indigo-500/20 text-indigo-700 dark:text-indigo-300 bg-indigo-500/5">{res.replace(/_/g, ' ')}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                {((provider.mutation_operations && provider.mutation_operations.length > 0) || 
                  (provider.read_operations && provider.read_operations.length > 0)) && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                      <Play className="w-4 h-4" /> Operations
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {provider.mutation_operations?.map(op => (
                        <Badge key={op} className="bg-amber-500/15 text-amber-700 dark:text-amber-400 hover:bg-amber-500/25 border-none font-medium">{op}</Badge>
                      ))}
                      {provider.read_operations?.map(op => (
                        <Badge key={op} variant="outline" className="text-[10px] font-mono">{op}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
