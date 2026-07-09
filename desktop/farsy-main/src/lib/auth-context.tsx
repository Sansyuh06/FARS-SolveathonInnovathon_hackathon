"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

export type UserRole = "admin" | "customer" | "operator";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  institutionName?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signup: (data: SignupData) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

interface SignupData {
  email: string;
  password: string;
  name: string;
  role: UserRole;
  institutionName?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEMO_USERS: (User & { password: string })[] = [
  { id: "1", email: "admin@fars.ai", password: "admin123", name: "Admin User", role: "admin" },
  { id: "2", email: "customer@hospital.com", password: "customer123", name: "Dr. Sarah Chen", role: "customer", institutionName: "Metro General Hospital" },
  { id: "3", email: "operator@fars.ai", password: "operator123", name: "Tech Operator", role: "operator" },
];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("fars_user");
    if (stored) {
      setUser(JSON.parse(stored));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    await new Promise((r) => setTimeout(r, 800));
    const found = DEMO_USERS.find((u) => u.email === email && u.password === password);
    if (found) {
      const { password: _, ...userData } = found;
      setUser(userData);
      localStorage.setItem("fars_user", JSON.stringify(userData));
      return { success: true };
    }
    return { success: false, error: "Invalid credentials" };
  };

  const signup = async (data: SignupData) => {
    await new Promise((r) => setTimeout(r, 800));
    const exists = DEMO_USERS.find((u) => u.email === data.email);
    if (exists) {
      return { success: false, error: "Email already registered" };
    }
    const newUser: User = {
      id: Date.now().toString(),
      email: data.email,
      name: data.name,
      role: data.role,
      institutionName: data.institutionName,
    };
    setUser(newUser);
    localStorage.setItem("fars_user", JSON.stringify(newUser));
    return { success: true };
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("fars_user");
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
