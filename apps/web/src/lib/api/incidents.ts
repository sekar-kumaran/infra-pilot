import { apiRequest } from "./client";
export const incidentsApi = {
  list: () => apiRequest("/incidents"),
  get: (id: string) => apiRequest(`/incidents/${id}`),
  acknowledge: (id: string) => apiRequest(`/incidents/${id}`, { method: "PATCH", body: JSON.stringify({ status: "ACKNOWLEDGED" }) }),
  resolve: (id: string) => apiRequest(`/incidents/${id}`, { method: "PATCH", body: JSON.stringify({ status: "RESOLVED" }) }),
};
