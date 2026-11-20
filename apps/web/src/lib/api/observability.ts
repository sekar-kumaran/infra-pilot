import { apiRequest } from "./client";
export const observabilityApi = {
  getLiveEvents: () => apiRequest("/events"),
  getLogs: (targetId: string, tail = 100) => apiRequest(`/resources/${targetId}/logs?tail=${tail}`),
};
