import { fetchApi } from './client';

export interface PolicyResponse {
  id: string;
  name: string;
  description?: string;
  enabled: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
  rules: any[]; // Or define PolicyRuleResponse
}

export interface PolicySimulationRequest {
  provider?: string;
  resource_id?: string;
  resource_type?: string;
  action?: string;
  risk?: string;
  severity?: string;
  environment?: string;
}

export interface PolicySimulationResponse {
  decision: string;
  risk?: string;
  matched_policies: string[];
  reason: string;
}

export const policiesApi = {
  list: async (): Promise<PolicyResponse[]> => {
    return fetchApi<PolicyResponse[]>('/policies');
  },
  simulate: async (request: PolicySimulationRequest): Promise<PolicySimulationResponse> => {
    return fetchApi<PolicySimulationResponse>('/policies/simulate', {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }
};
