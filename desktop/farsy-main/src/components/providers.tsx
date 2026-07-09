"use client";

import { ReactNode } from "react";
import { ThemeProvider } from "./theme-provider";
import { AuthProvider } from "@/lib/auth-context";
import { RobotStoreProvider } from "@/lib/robot-store";
import { Toaster } from "@/components/ui/sonner";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <RobotStoreProvider>
          {children}
          <Toaster position="top-right" />
        </RobotStoreProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
