import { fetchApi } from './client';

export interface AuditLogResponse {
  id: string;
  actor_id?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  result: string;
  request_id?: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export const auditApi = {
  list: async (params?: Record<string, string>): Promise<AuditLogResponse[]> => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<AuditLogResponse[]>(`/audit${query}`);
  }
};
