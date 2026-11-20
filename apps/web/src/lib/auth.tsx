import React, { createContext, useContext, useState, useEffect } from "react";

export interface AuthUser {
  id: string;
  email: string;
  role: "SUPER_ADMIN" | "ADMIN" | "DEVELOPER" | "VIEWER";
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, role?: AuthUser["role"]) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: { id: "usr-01", email: "superadmin@infrapilot.io", role: "SUPER_ADMIN" },
  loading: false,
  login: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>({
    id: "usr-01",
    email: "superadmin@infrapilot.io",
    role: "SUPER_ADMIN",
  });
  return (
    <AuthContext.Provider
      value={{
        user,
        loading: false,
        login: (email, role = "SUPER_ADMIN") => setUser({ id: "usr-01", email, role }),
        logout: () => setUser(null),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
