import { fetchApi } from './client';
import { AsyncJobResponse } from './integrations';

export interface RawEventResponse {
  id: string;
  provider: string;
  event_type: string;
  source_id: string;
  payload: Record<string, any>;
  received_at: string;
  occurred_at?: string;
  processing_status: string;
  processing_result?: string;
  resource_id?: string;
  integration_id?: string;
}

export const eventsApi = {
  list: async (params?: Record<string, string>): Promise<RawEventResponse[]> => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<RawEventResponse[]>(`/events${query}`);
  },

  get: async (id: string): Promise<RawEventResponse> => {
    return fetchApi<RawEventResponse>(`/events/${id}`);
  },

  reprocess: async (id: string): Promise<AsyncJobResponse> => {
    return fetchApi<AsyncJobResponse>(`/events/${id}/reprocess`, {
      method: 'POST',
    });
  }
};
