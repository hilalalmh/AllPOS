import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuthStore } from "../stores/authStore";

export default function RequireRole({
  role,
  children,
}: {
  role: "OWNER" | "KASIR";
  children: ReactNode;
}) {
  const user = useAuthStore((s) => s.user);
  if (user?.role !== role) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}