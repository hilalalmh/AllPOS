import { useCallback, useEffect, useState, type FormEvent } from "react";

import {
  EmptyState,
  ErrorAlert,
  Modal,
  Spinner,
  StatusBadge,
} from "../components/ui";
import {
  cancelTransaction,
  fetchTransactions,
} from "../services/transactions";
import { downloadReport } from "../services/audit";
import type {
  PaymentMethod,
  Transaction,
  TransactionList,
} from "../types";
import { formatDateTime, formatRupiah, todayISO } from "../utils/format";
import { useAuthStore } from "../stores/authStore";

const STATUSES = ["PAID", "PENDING", "CANCELLED"] as const;
const METHODS: PaymentMethod[] = ["CASH", "QRIS", "TRANSFER"];
const PAGE_SIZE = 10;

const PAYMENT_LABELS: Record<PaymentMethod, string> = {
  CASH: "Tunai",
  QRIS: "QRIS",
  TRANSFER: "Transfer",
};

export default function TransactionsPage() {
  const isOwner = useAuthStore((s) => s.user?.role === "OWNER");
  const [data, setData] = useState<TransactionList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [method, setMethod] = useState("");
  const [startDate, setStartDate] = useState(todayISO());
  const [endDate, setEndDate] = useState(todayISO());
  const [page, setPage] = useState(1);

  const [selected, setSelected] = useState<Transaction | null>(null);
  const [cancelling, setCancelling] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchTransactions({
        q: q || undefined,
        status: status || undefined,
        payment_method: method || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        page,
        page_size: PAGE_SIZE,
      });
      setData(res);
    } catch (err) {
      console.error(err);
      setError("Gagal memuat transaksi.");
    } finally {
      setLoading(false);
    }
  }, [q, status, method, startDate, endDate, page]);

  useEffect(() => {
    void load();
  }, [load]);

  function handleRefresh(e: FormEvent) {
    e.preventDefault();
    setPage(1);
    void load();
  }

  async function handleExport(format: "csv" | "pdf") {
    setError(null);
    try {
      await downloadReport(format, {
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        payment_method: method || undefined,
        status: status || undefined,
      });
    } catch (err) {
      console.error(err);
      setError("Gagal mengunduh laporan.");
    }
  }

  async function handleCancel() {
    if (!selected) return;
    setCancelling(true);
    try {
      const updated = await cancelTransaction(selected.id);
      setSelected(updated);
      await load();
    } catch (err) {
      console.error(err);
      setError("Gagal membatalkan transaksi.");
    } finally {
      setCancelling(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Transaksi</h1>

      {error && <ErrorAlert message={error} />}

      <form
        onSubmit={handleRefresh}
        className="flex flex-wrap gap-2 rounded-lg bg-white p-3 shadow"
      >
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Cari invoice..."
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">Semua status</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={method}
          onChange={(e) => setMethod(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">Semua metode</option>
          {METHODS.map((m) => (
            <option key={m} value={m}>
              {PAYMENT_LABELS[m]}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
        <span className="py-2 text-sm text-gray-400">s/d</span>
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          Terapkan
        </button>
        <span className="hidden w-px bg-gray-200 sm:block" />
        {isOwner && (
          <>
            <button
              type="button"
              onClick={() => handleExport("csv")}
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Export CSV
            </button>
            <button
              type="button"
              onClick={() => handleExport("pdf")}
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Export PDF
            </button>
          </>
        )}
      </form>

      {loading ? (
        <Spinner />
      ) : !data || data.items.length === 0 ? (
        <EmptyState message="Belum ada transaksi pada filter ini." />
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg bg-white shadow">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-gray-500">
                  <th className="px-4 py-3">Invoice</th>
                  <th className="px-4 py-3">Waktu</th>
                  <th className="px-4 py-3">Metode</th>
                  <th className="px-4 py-3 text-right">Total</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((tx) => (
                  <tr key={tx.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">
                      {tx.invoice_number}
                    </td>
                    <td className="px-4 py-3">
                      {formatDateTime(tx.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      {PAYMENT_LABELS[tx.payment_method as PaymentMethod] ??
                        tx.payment_method}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold">
                      {formatRupiah(tx.total)}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={tx.status} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setSelected(tx)}
                        className="text-emerald-700 hover:underline"
                      >
                        Detail
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>
              Halaman {data.page} dari {Math.max(1, Math.ceil(data.total / PAGE_SIZE))}{" "}
              ({data.total} transaksi)
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="rounded-md border border-gray-300 px-3 py-1 disabled:opacity-40"
              >
                Sebelumnya
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * PAGE_SIZE >= data.total}
                className="rounded-md border border-gray-300 px-3 py-1 disabled:opacity-40"
              >
                Berikutnya
              </button>
            </div>
          </div>
        </>
      )}

      {selected && (
        <Modal
          open
          title={selected.invoice_number}
          onClose={() => setSelected(null)}
        >
          <dl className="space-y-1.5 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">Status</dt>
              <dd>
                <StatusBadge status={selected.status} />
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Waktu</dt>
              <dd>{formatDateTime(selected.created_at)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Kasir</dt>
              <dd>#{selected.cashier_id}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Metode</dt>
              <dd>
                {PAYMENT_LABELS[selected.payment_method as PaymentMethod] ??
                  selected.payment_method}
              </dd>
            </div>
          </dl>

          <div className="my-4 border-t" />

          <ul className="space-y-2 text-sm">
            {selected.items.map((item) => (
              <li key={item.id} className="flex justify-between gap-2">
                <span>
                  {item.quantity}x {item.product_name}
                </span>
                <span className="font-medium">{formatRupiah(item.subtotal)}</span>
              </li>
            ))}
          </ul>

          <div className="mt-4 space-y-1 border-t pt-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Subtotal</span>
              <span>{formatRupiah(selected.subtotal)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Diskon</span>
              <span>-{formatRupiah(selected.discount)}</span>
            </div>
            <div className="flex justify-between text-base font-bold">
              <span>Total</span>
              <span>{formatRupiah(selected.total)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Dibayar</span>
              <span>{formatRupiah(selected.paid_amount)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Kembalian</span>
              <span>{formatRupiah(selected.change_amount)}</span>
            </div>
          </div>

          {selected.status !== "CANCELLED" && (
            <button
              onClick={handleCancel}
              disabled={cancelling}
              className="mt-4 w-full rounded-md bg-red-600 px-4 py-2 font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              {cancelling ? "Membatalkan..." : "Batalkan Transaksi"}
            </button>
          )}
        </Modal>
      )}
    </div>
  );
}