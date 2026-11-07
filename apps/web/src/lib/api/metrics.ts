import { fetchApi } from './client';

export interface SystemMetricsResponse {
  events_processed: number;
  failed_events: number;
  active_alerts: number;
  open_incidents: number;
  critical_incidents: number;
  active_integrations: number;
  automation_executions: number;
  failed_executions: number;
}

export const metricsApi = {
  getSummary: async (): Promise<SystemMetricsResponse> => {
    return fetchApi<SystemMetricsResponse>('/system/metrics-summary');
  }
};
