import { apiRequest } from "./client";
export const auditApi = {
  list: (limit = 100) => apiRequest(`/audit?limit=${limit}`),
};
