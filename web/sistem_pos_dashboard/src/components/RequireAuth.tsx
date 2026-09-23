import { useEffect, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuthStore } from "../stores/authStore";

export default function RequireAuth({ children }: { children: ReactNode }) {
  const { user, booting, loadMe } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
    if (window.localStorage.getItem("pos_access_token")) {
      void loadMe();
    } else {
      useAuthStore.setState({ booting: false });
    }
  }, [loadMe]);

  useEffect(() => {
    const onExpired = () => useAuthStore.getState().logout();
    window.addEventListener("auth-expired", onExpired);
    return () => window.removeEventListener("auth-expired", onExpired);
  }, []);

  if (window.localStorage.getItem("pos_access_token") && booting && !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100 text-gray-500">
        Memuat...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
}