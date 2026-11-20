import { apiRequest } from "./client";
export const resourcesApi = {
  list: () => apiRequest("/resources"),
  get: (id: string) => apiRequest(`/resources/${id}`),
  exec: (id: string, command: string, shell = "bash") => apiRequest(`/resources/${id}/exec`, { method: "POST", body: JSON.stringify({ command, shell }) }),
  logs: (id: string, tail = 100) => apiRequest(`/resources/${id}/logs?tail=${tail}`),
};
