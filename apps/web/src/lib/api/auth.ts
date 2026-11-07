import { fetchApi } from './client';

export interface UserResponse {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  role: string;
  permissions: string[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export const authApi = {
  login: async (credentials: any): Promise<TokenResponse> => {
    return fetchApi<TokenResponse>('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });
  },

  register: async (data: any): Promise<UserResponse> => {
    return fetchApi<UserResponse>('/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
  },

  getCurrentUser: async (): Promise<UserResponse> => {
    return fetchApi<UserResponse>('/auth/me', {
      method: 'GET',
    });
  }
};
