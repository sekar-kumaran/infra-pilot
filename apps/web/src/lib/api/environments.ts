import { fetchApi } from './client';

export interface EnvironmentResponse {
  id: string;
  name: string;
  description?: string;
  environment_type: string;
  is_active: boolean;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface EnvironmentCreate {
  name: string;
  description?: string;
  environment_type: string;
  is_active?: boolean;
  metadata?: Record<string, any>;
}

export const environmentsApi = {
  list: async (): Promise<EnvironmentResponse[]> => {
    const res = await fetchApi<{ items: EnvironmentResponse[] }>('/environments');
    return res.items || [];
  },

  get: async (id: string): Promise<EnvironmentResponse> => {
    return fetchApi<EnvironmentResponse>(`/environments/${id}`);
  },

  create: async (data: EnvironmentCreate): Promise<EnvironmentResponse> => {
    return fetchApi<EnvironmentResponse>('/environments', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: async (id: string, data: Partial<EnvironmentCreate>): Promise<EnvironmentResponse> => {
    return fetchApi<EnvironmentResponse>(`/environments/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: async (id: string): Promise<void> => {
    return fetchApi<void>(`/environments/${id}`, {
      method: 'DELETE',
    });
  }
};
