import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ErrorAlert, Spinner, StatCard } from "../components/ui";
import {
  fetchBestSellers,
  fetchSales,
  fetchSummary,
} from "../services/dashboard";
import type {
  BestSellerItem,
  DashboardSummary,
  SalesPoint,
} from "../types";
import { formatMoney, formatRupiah, toISODate } from "../utils/format";

type Period = "today" | "7d" | "30d";

const RANGES: Record<Period, number> = {
  today: 0,
  "7d": 7,
  "30d": 30,
};

function rangeDates(period: Period): { start: string; end: string } {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - RANGES[period]);
  return { start: toISODate(start), end: toISODate(end) };
}

export default function HomePage() {
  const [period, setPeriod] = useState<Period>("today");
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [sales, setSales] = useState<SalesPoint[]>([]);
  const [best, setBest] = useState<BestSellerItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const { start, end } = rangeDates(period);

    Promise.all([
      fetchSummary(start, end),
      fetchSales(start, end, period === "30d" ? "month" : "day"),
      fetchBestSellers(start, end),
    ])
      .then(([s, salesData, bestData]) => {
        if (cancelled) return;
        setSummary(s);
        setSales(salesData);
        setBest(bestData.items);
      })
      .catch((err) => {
        if (cancelled) return;
        setError("Gagal memuat statistik dashboard.");
        console.error(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [period]);

  if (loading) return <Spinner />;
  if (error) return <ErrorAlert message={error} />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        <div className="flex gap-1 rounded-md bg-white p-1 shadow">
          {(["today", "7d", "30d"] as Period[]).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`rounded px-3 py-1 text-sm ${
                period === p
                  ? "bg-emerald-600 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              {p === "today" ? "Hari Ini" : p === "7d" ? "7 Hari" : "30 Hari"}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Total Penjualan"
          value={formatRupiah(summary?.sales_total ?? 0)}
          hint={`${summary?.start_date} s/d ${summary?.end_date}`}
        />
        <StatCard
          label="Transaksi"
          value={String(summary?.transaction_count ?? 0)}
          hint={`${summary?.item_count ?? 0} item terjual`}
        />
        <StatCard
          label="Produk Aktif"
          value={String(summary?.active_products ?? 0)}
          hint="total menu"
        />
        <StatCard
          label="Terlaris"
          value={summary?.best_seller?.product_name ?? "-"}
          hint={
            summary?.best_seller
              ? `${summary.best_seller.quantity}x terjual`
              : "belum ada transaksi"
          }
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-lg bg-white p-5 shadow lg:col-span-2">
          <h2 className="mb-4 font-semibold text-gray-700">Penjualan</h2>
          {sales.length === 0 ? (
            <p className="py-10 text-center text-sm text-gray-400">
              Belum ada data penjualan pada periode ini.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={sales}>
                <defs>
                  <linearGradient id="sales" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#059669" stopOpacity={0.6} />
                    <stop offset="95%" stopColor="#059669" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="period" tick={{ fontSize: 12 }} />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(v) => formatMoney(Number(v))}
                />
                <Tooltip formatter={(v) => formatRupiah(Number(v))} />
                <Area
                  type="monotone"
                  dataKey="sales_total"
                  name="Penjualan"
                  stroke="#059669"
                  fill="url(#sales)"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-lg bg-white p-5 shadow">
          <h2 className="mb-4 font-semibold text-gray-700">Menu Terlaris</h2>
          {best.length === 0 ? (
            <p className="py-10 text-center text-sm text-gray-400">
              Belum ada penjualan.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart
                data={best}
                layout="vertical"
                margin={{ left: 8, right: 16 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" hide />
                <YAxis
                  type="category"
                  dataKey="product_name"
                  width={90}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip formatter={(v, n) => [v, n === "quantity" ? "Jumlah" : "Pendapatan"]} />
                <Legend />
                <Bar dataKey="quantity" name="Jumlah" fill="#059669" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}