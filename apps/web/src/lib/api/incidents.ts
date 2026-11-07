import { fetchApi } from './client';
import { AlertResponse } from './alerts';
import { InfrastructureResourceResponse } from './resources';

export interface IncidentResponse {
  id: string;
  title: string;
  description?: string;
  status: string;
  severity: string;
  priority: string;
  primary_resource_id?: string;
  opened_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
}

export interface IncidentEventResponse {
  id: string;
  incident_id: string;
  event_type: string;
  message: string;
  actor_id?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface IncidentDetailResponse extends IncidentResponse {
  events: IncidentEventResponse[];
  alerts: AlertResponse[];
  resources: InfrastructureResourceResponse[];
  // automation_executions will be populated via a separate automation API or included here if the backend does it
}

export const incidentsApi = {
  list: async (params?: Record<string, string>): Promise<IncidentResponse[]> => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<IncidentResponse[]>(`/incidents${query}`);
  },

  get: async (id: string): Promise<IncidentDetailResponse> => {
    return fetchApi<IncidentDetailResponse>(`/incidents/${id}`);
  },

  acknowledge: async (id: string): Promise<IncidentResponse> => {
    return fetchApi<IncidentResponse>(`/incidents/${id}/acknowledge`, {
      method: 'POST',
    });
  },

  updateStatus: async (id: string, status: string): Promise<IncidentResponse> => {
    return fetchApi<IncidentResponse>(`/incidents/${id}/status`, {
      method: 'POST',
      body: JSON.stringify({ status }),
    });
  },

  resolve: async (id: string): Promise<IncidentResponse> => {
    return fetchApi<IncidentResponse>(`/incidents/${id}/resolve`, {
      method: 'POST',
    });
  }
};
