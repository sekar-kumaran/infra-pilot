import { apiRequest } from "./client";
export const environmentsApi = {
  list: () => apiRequest("/environments"),
  get: (id: string) => apiRequest(`/environments/${id}`),
};
