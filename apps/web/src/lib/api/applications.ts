import { apiRequest } from "./client";
export const applicationsApi = {
  list: () => apiRequest("/applications"),
  get: (id: string) => apiRequest(`/applications/${id}`),
  create: (data: any) => apiRequest("/applications", { method: "POST", body: JSON.stringify(data) }),
  getResources: (id: string) => apiRequest(`/applications/${id}/resources`),
};
