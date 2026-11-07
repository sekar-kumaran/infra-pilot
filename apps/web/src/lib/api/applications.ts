import { fetchApi } from './client';
import { InfrastructureResourceResponse } from './resources';

export interface ApplicationResponse {
  id: string;
  name: string;
  description?: string;
  status: string;
  created_at: string;
  updated_at: string;
  resource_count: number;
  incidents_count: number;
}

export interface ApplicationCreate {
  name: string;
  description?: string;
  status?: string;
}

export const applicationsApi = {
  list: async (params?: Record<string, string>): Promise<ApplicationResponse[]> => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<ApplicationResponse[]>(`/applications${query}`);
  },

  get: async (id: string): Promise<ApplicationResponse> => {
    return fetchApi<ApplicationResponse>(`/applications/${id}`);
  },

  create: async (data: ApplicationCreate): Promise<ApplicationResponse> => {
    return fetchApi<ApplicationResponse>('/applications', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: async (id: string, data: Partial<ApplicationCreate>): Promise<ApplicationResponse> => {
    return fetchApi<ApplicationResponse>(`/applications/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: async (id: string): Promise<void> => {
    return fetchApi<void>(`/applications/${id}`, {
      method: 'DELETE',
    });
  },

  getResources: async (id: string): Promise<InfrastructureResourceResponse[]> => {
    return fetchApi<InfrastructureResourceResponse[]>(`/applications/${id}/resources`);
  }
};
