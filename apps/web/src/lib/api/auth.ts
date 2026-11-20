import { apiRequest } from "./client";
export const authApi = {
  login: (data: { email: string; password: string }) => apiRequest("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  register: (data: { email: string; password: string; role?: string }) => apiRequest("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  me: () => apiRequest("/auth/me"),
};
