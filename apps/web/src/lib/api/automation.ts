import { fetchApi } from './client';

export interface PlaybookStepResponse {
  id: string;
  step_order: number;
  name: string;
  action_name: string;
  action_type: string;
  parameters: Record<string, any>;
  verification_config?: string;
  timeout_seconds: number;
  continue_on_failure: boolean;
  risk_level: string;
}

export interface PlaybookResponse {
  id: string;
  name: string;
  description?: string;
  version: number;
  status: string;
  trigger_type: string;
  steps: PlaybookStepResponse[];
  created_at: string;
  updated_at: string;
}

export interface AutomationExecutionResponse {
  id: string;
  workflow_id: string;
  playbook_id?: string;
  incident_id?: string;
  resource_id?: string;
  status: string;
  risk_level?: string;
  current_step_id?: string;
  started_at?: string;
  completed_at?: string;
  failure_reason?: string;
  error_classification?: string;
  retry_count: number;
  last_attempt_at?: string;
  next_retry_at?: string;
  created_at: string;
  updated_at: string;
  workflow?: PlaybookResponse;
  playbook?: { name: string };
  step_executions: any[];
}

export interface AutomationApprovalResponse {
  id: string;
  execution_id: string;
  approver_role?: string;
  status: string;
  decision_reason?: string;
  expires_at: string;
  created_at: string;
  updated_at: string;
  execution?: AutomationExecutionResponse;
}

export const automationApi = {
  getPlaybooks: async (): Promise<PlaybookResponse[]> => {
    return fetchApi<PlaybookResponse[]>('/automation/playbooks');
  },

  createPlaybook: async (data: {
    name: string;
    description?: string;
    trigger_type?: string;
    version?: number;
    steps?: Array<{ name: string; action_name: string; action_type?: string; risk_level?: string; parameters?: Record<string, any> }>;
  }): Promise<PlaybookResponse> => {
    return fetchApi<PlaybookResponse>('/automation/playbooks', {
      method: 'POST',
      body: JSON.stringify({
        trigger_type: 'MANUAL',
        version: 1,
        ...data,
      }),
    });
  },

  getTemplates: async (): Promise<any[]> => {
    return fetchApi<any[]>('/automation/templates');
  },

  getAutomationExecutions: async (): Promise<any[]> => {
    return fetchApi<any[]>('/automation/executions');
  },

  getExecutions: async (): Promise<AutomationExecutionResponse[]> => {
    try {
      const wfExecs = await fetchApi<AutomationExecutionResponse[]>('/workflows/executions');
      if (wfExecs && wfExecs.length > 0) return wfExecs;
    } catch (_) {}
    return fetchApi<AutomationExecutionResponse[]>('/automation/executions');
  },

  getApprovals: async (): Promise<AutomationApprovalResponse[]> => {
    return fetchApi<AutomationApprovalResponse[]>('/automation/approvals');
  },

  triggerExecution: async (data: {
    playbook_id: string;
    trigger_type?: string;
    trigger_source?: string;
    incident_id?: string;
    resource_id?: string;
  }): Promise<AutomationExecutionResponse> => {
    return fetchApi<AutomationExecutionResponse>('/automation/executions', {
      method: 'POST',
      body: JSON.stringify({
        trigger_type: 'MANUAL',
        trigger_source: 'web_console',
        ...data,
      }),
    });
  },

  resumeExecution: async (executionId: string): Promise<any> => {
    return fetchApi<any>(`/workflows/executions/${executionId}/resume`, {
      method: 'POST',
    });
  },

  approveExecution: async (id: string, reason?: string): Promise<AutomationApprovalResponse> => {
    return fetchApi<AutomationApprovalResponse>(`/automation/approvals/${id}/action`, {
      method: 'POST',
      body: JSON.stringify({ action: 'APPROVE', reason: reason || 'Approved via console' }),
    });
  },

  rejectExecution: async (id: string, reason: string): Promise<AutomationApprovalResponse> => {
    return fetchApi<AutomationApprovalResponse>(`/automation/approvals/${id}/action`, {
      method: 'POST',
      body: JSON.stringify({ action: 'REJECT', reason }),
    });
  }
};
