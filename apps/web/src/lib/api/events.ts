import { apiRequest } from "./client";
export const eventsApi = {
  list: () => apiRequest("/events"),
  reprocess: (id: string) => apiRequest(`/events/${id}/reprocess`, { method: "POST" }),
};
