import { apiRequest } from "./client";
export const alertsApi = {
  list: (params?: Record<string, string>) => apiRequest("/alerts"),
  get: (id: string) => apiRequest(`/alerts/${id}`),
  acknowledge: (id: string) => apiRequest(`/alerts/${id}/acknowledge`, { method: "POST" }),
  resolve: (id: string) => apiRequest(`/alerts/${id}/resolve`, { method: "POST" }),
};
