import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuthStore } from "../stores/authStore";

const kasirNav = [
  { to: "/pos", label: "Kasir & Bayar" },
  { to: "/transactions", label: "Transaksi" },
];

const ownerNav = [
  { to: "/", label: "Dashboard" },
  { to: "/pos", label: "Kasir & Bayar" },
  { to: "/transactions", label: "Transaksi" },
  { to: "/products", label: "Produk" },
  { to: "/categories", label: "Kategori" },
  { to: "/store-profile", label: "Profil Toko" },
  { to: "/audit", label: "Audit Trail" },
  { to: "/health", label: "Health Check" },
];

export default function DashboardLayout() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const isOwner = user?.role === "OWNER";
  const navItems = isOwner ? ownerNav : kasirNav;

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-emerald-700 text-white shadow">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3">
          <span className="text-lg font-semibold">Sistem POS</span>
          <div className="flex flex-1 flex-wrap gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `px-3 py-1 text-sm rounded-md transition ${
                    isActive
                      ? "bg-emerald-800 font-medium"
                      : "opacity-80 hover:bg-emerald-800 hover:opacity-100"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm sm:block">
              {user?.full_name}
              <span className="ml-1 text-xs opacity-70">({user?.role})</span>
            </span>
            <button
              onClick={handleLogout}
              className="rounded-md bg-emerald-800 px-3 py-1 text-sm hover:bg-emerald-900"
            >
              Keluar
            </button>
          </div>
        </div>
      </nav>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}