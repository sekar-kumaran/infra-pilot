import { apiRequest } from "./client";
export const integrationsApi = {
  list: () => apiRequest("/integrations"),
  create: (data: any) => apiRequest("/integrations", { method: "POST", body: JSON.stringify(data) }),
  enable: (id: string) => apiRequest(`/integrations/${id}/enable`, { method: "POST" }),
  disable: (id: string) => apiRequest(`/integrations/${id}/disable`, { method: "POST" }),
  validate: (id: string) => apiRequest(`/integrations/${id}/validate`, { method: "POST" }),
  discover: (id: string) => apiRequest(`/integrations/${id}/discover`, { method: "POST" }),
};
