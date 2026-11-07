import { fetchApi } from './client';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: string;
  service: string;
  message: string;
  metadata: Record<string, string>;
}

export interface LiveEvent {
  id: string;
  timestamp: string;
  type: string;
  description: string;
  source: string;
}

export const observabilityApi = {
  getLogs: async (query?: string, level?: string, limit: number = 50): Promise<LogEntry[]> => {
    let url = `/observability/logs?limit=${limit}`;
    if (query) url += `&query=${encodeURIComponent(query)}`;
    if (level) url += `&level=${level}`;
    const res = await fetchApi(url) as any;
    return res.items || [];
  },

  getLiveEvents: async (limit: number = 20): Promise<LiveEvent[]> => {
    const res = await fetchApi(`/observability/live-events?limit=${limit}`) as any;
    return res.items || [];
  }
};
