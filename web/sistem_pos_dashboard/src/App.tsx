import { Navigate, Route, Routes } from "react-router-dom";

import RequireAuth from "./components/RequireAuth";
import RequireRole from "./components/RequireRole";
import DashboardLayout from "./layouts/DashboardLayout";
import AuditTrailPage from "./pages/AuditTrailPage";
import CategoriesPage from "./pages/CategoriesPage";
import HealthPage from "./pages/HealthPage";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import PosPage from "./pages/PosPage";
import ProductsPage from "./pages/ProductsPage";
import StoreProfilePage from "./pages/StoreProfilePage";
import TransactionsPage from "./pages/TransactionsPage";
import UsersPage from "./pages/UsersPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <RequireAuth>
            <DashboardLayout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<HomePage />} />
        <Route path="/pos" element={<PosPage />} />
        <Route path="/transactions" element={<TransactionsPage />} />
        <Route
          path="/products"
          element={
            <RequireRole role="OWNER">
              <ProductsPage />
            </RequireRole>
          }
        />
        <Route
          path="/categories"
          element={
            <RequireRole role="OWNER">
              <CategoriesPage />
            </RequireRole>
          }
        />
        <Route
          path="/store-profile"
          element={
            <RequireRole role="OWNER">
              <StoreProfilePage />
            </RequireRole>
          }
        />
        <Route
          path="/users"
          element={
            <RequireRole role="OWNER">
              <UsersPage />
            </RequireRole>
          }
        />
        <Route
          path="/audit"
          element={
            <RequireRole role="OWNER">
              <AuditTrailPage />
            </RequireRole>
          }
        />
        <Route
          path="/health"
          element={
            <RequireRole role="OWNER">
              <HealthPage />
            </RequireRole>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}