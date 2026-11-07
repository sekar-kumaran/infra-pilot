import { fetchApi } from './client';

export interface AlertResponse {
  id: string;
  title: string;
  severity: string;
  status: string;
  provider: string;
  fingerprint: string;
  source_event_id: string;
  resource_id?: string;
  incident_id?: string;
  metadata?: Record<string, any>;
  started_at: string;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
}

export const alertsApi = {
  list: async (params?: Record<string, string>): Promise<AlertResponse[]> => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<AlertResponse[]>(`/alerts${query}`);
  },

  get: async (id: string): Promise<AlertResponse> => {
    return fetchApi<AlertResponse>(`/alerts/${id}`);
  },

  acknowledge: async (id: string): Promise<AlertResponse> => {
    return fetchApi<AlertResponse>(`/alerts/${id}/acknowledge`, {
      method: 'POST',
    });
  },

  resolve: async (id: string): Promise<AlertResponse> => {
    return fetchApi<AlertResponse>(`/alerts/${id}/resolve`, {
      method: 'POST',
    });
  }
};
