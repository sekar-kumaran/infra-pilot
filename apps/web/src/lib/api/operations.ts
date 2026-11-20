import { apiRequest } from "./client";
export const operationsApi = {
  getWorkers: () => apiRequest("/operations/workers"),
  getQueues: () => apiRequest("/operations/queues"),
};
