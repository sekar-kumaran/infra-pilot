import { apiRequest } from "./client";
export const policiesApi = {
  list: () => apiRequest("/policies"),
  simulate: (context: any) => apiRequest("/policies/simulate", { method: "POST", body: JSON.stringify(context) }),
};
