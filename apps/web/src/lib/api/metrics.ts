import { apiRequest } from "./client";
export const metricsApi = {
  getSummary: () => apiRequest("/system/metrics-summary"),
};
