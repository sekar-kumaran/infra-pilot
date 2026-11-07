import { fetchApi } from './client';

export interface IntegrationResponse {
  id: string;
  name: string;
  provider: string;
  status: string;
  created_at: string;
  updated_at: string;
  last_checked_at?: string;
  circuit_state: string;
  failure_count: number;
  last_failure_at?: string;
}

export interface IntegrationCreate {
  name: string;
  provider: string;
  description?: string;
  configuration: Record<string, any>;
}

export interface ValidationResponse {
  is_valid: boolean;
  message: string;
}

export interface AsyncJobResponse {
  message: string;
  job_id: string;
}

export const integrationsApi = {
  list: async (params?: Record<string, string>): Promise<IntegrationResponse[]> => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<IntegrationResponse[]>(`/integrations${query}`);
  },

  get: async (id: string): Promise<IntegrationResponse> => {
    return fetchApi<IntegrationResponse>(`/integrations/${id}`);
  },

  create: async (data: IntegrationCreate): Promise<IntegrationResponse> => {
    return fetchApi<IntegrationResponse>('/integrations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  validate: async (id: string): Promise<ValidationResponse> => {
    return fetchApi<ValidationResponse>(`/integrations/${id}/validate`, {
      method: 'POST',
    });
  },

  enable: async (id: string): Promise<IntegrationResponse> => {
    return fetchApi<IntegrationResponse>(`/integrations/${id}/enable`, {
      method: 'POST',
    });
  },

  disable: async (id: string): Promise<IntegrationResponse> => {
    return fetchApi<IntegrationResponse>(`/integrations/${id}/disable`, {
      method: 'POST',
    });
  },

  discover: async (id: string): Promise<AsyncJobResponse> => {
    return fetchApi<AsyncJobResponse>(`/integrations/${id}/discover`, {
      method: 'POST',
    });
  },

  getMetrics: async (id: string, metric_type: string): Promise<any> => {
    return fetchApi<any>(`/integrations/${id}/metrics?metric_type=${encodeURIComponent(metric_type)}`, {
      method: 'GET',
    });
  }
};
