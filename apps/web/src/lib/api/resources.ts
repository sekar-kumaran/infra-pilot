import { fetchApi } from './client';

export interface InfrastructureResourceResponse {
  id: string;
  name: string;
  display_name: string;
  resource_type: string;
  provider: string;
  status: string;
  external_id?: string;
  environment_id: string;
  metadata?: Record<string, any>;
  tags?: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export const resourcesApi = {
  list: async (params?: Record<string, string>): Promise<InfrastructureResourceResponse[]> => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    const res = await fetchApi<any>(`/resources${query}`);
    return res.items || [];
  },

  get: async (id: string): Promise<InfrastructureResourceResponse> => {
    return fetchApi<InfrastructureResourceResponse>(`/resources/${id}`);
  },

  getHistory: async (id: string): Promise<any[]> => {
    return fetchApi<any[]>(`/resources/${id}/history`);
  }
};
