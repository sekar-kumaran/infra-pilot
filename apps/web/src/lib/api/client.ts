const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  public status: number;
  public data: any;
  public code?: string;
  public requestId?: string;

  constructor(status: number, data: any) {
    const message = data?.error?.message || data?.detail || 'An unexpected API error occurred';
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    this.code = data?.error?.code;
    this.requestId = data?.error?.request_id;
  }
}

let _token: string | null = null;

export const setAuthToken = (token: string | null) => {
  _token = token;
  if (token) {
    // We document that local storage is used because the FastAPI backend
    // expects a Bearer token (not an HttpOnly cookie) and a BFF proxy would be 
    // over-architecting for this phase.
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  } else {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }
};

export const getAuthToken = (): string | null => {
  if (_token) return _token;
  if (typeof window !== 'undefined') {
    return localStorage.getItem('auth_token');
  }
  return null;
};

export const clearAuthToken = () => {
  setAuthToken(null);
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
};

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = getAuthToken();

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  } as Record<string, string>;

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Remove Content-Type if it's FormData (browser will set it with boundary)
  if (options.body instanceof FormData) {
    delete (headers as Record<string, string>)['Content-Type'];
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      clearAuthToken();
      throw new ApiError(401, { detail: 'Unauthorized. Please log in again.' });
    }
    
    if (response.status === 403) {
      // Don't auto-logout on 403, just throw the error
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(403, errorData);
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(response.status, errorData);
    }

    // For 204 No Content or empty responses
    const text = await response.text();
    if (!text) {
      return {} as T;
    }

    return JSON.parse(text) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(500, { detail: error instanceof Error ? error.message : 'Network error' });
  }
}
