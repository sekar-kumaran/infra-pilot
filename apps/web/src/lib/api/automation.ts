import { apiRequest } from "./client";
export const automationApi = {
  getApprovals: () => apiRequest("/automation/approvals"),
  getExecutions: () => apiRequest("/automation/executions"),
  getPlaybooks: () => apiRequest("/automation/playbooks"),
  getTemplates: () => apiRequest("/automation/playbooks"),
  approveExecution: (id: string, reason = "Approved in UI") => apiRequest(`/automation/approvals/${id}/action`, { method: "POST", body: JSON.stringify({ action: "APPROVE", reason }) }),
  rejectExecution: (id: string, reason = "Rejected in UI") => apiRequest(`/automation/approvals/${id}/action`, { method: "POST", body: JSON.stringify({ action: "REJECT", reason }) }),
};
