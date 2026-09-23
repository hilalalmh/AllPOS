import { Navigate, Route, Routes } from "react-router-dom";

import RequireAuth from "./components/RequireAuth";
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
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/categories" element={<CategoriesPage />} />
        <Route path="/store-profile" element={<StoreProfilePage />} />
        <Route path="/audit" element={<AuditTrailPage />} />
        <Route path="/health" element={<HealthPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}