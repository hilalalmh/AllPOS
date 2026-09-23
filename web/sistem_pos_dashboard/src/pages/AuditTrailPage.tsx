import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";

import {
  EmptyState,
  ErrorAlert,
  Spinner,
} from "../components/ui";
import { fetchAuditLogs } from "../services/audit";
import type { AuditLogList } from "../types";
import { formatDateTime } from "../utils/format";

const ACTIONS = [
  "auth.login",
  "transaction.create",
  "transaction.cancel",
  "product.create",
  "product.update",
  "product.delete",
  "category.create",
  "category.update",
  "category.delete",
  "store_profile.update",
  "report.csv",
  "report.pdf",
];

const ENTITY_TYPES = [
  "user",
  "transaction",
  "product",
  "category",
  "store_profile",
  "report",
];

const PAGE_SIZE = 20;

export default function AuditTrailPage() {
  const [data, setData] = useState<AuditLogList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [page, setPage] = useState(1);
  const [reloadKey, setReloadKey] = useState(0);
  const seqRef = useRef(0);

  const load = useCallback(async () => {
    const seq = ++seqRef.current;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchAuditLogs({
        action: action || undefined,
        entity_type: entityType || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        page,
        page_size: PAGE_SIZE,
      });
      if (seq === seqRef.current) setData(res);
    } catch (err) {
      if (seq === seqRef.current) {
        console.error(err);
        setError("Gagal memuat audit trail.");
      }
    } finally {
      if (seq === seqRef.current) setLoading(false);
    }
  }, [action, entityType, startDate, endDate, page, reloadKey]);

  useEffect(() => {
    setPage(1);
  }, [action, entityType, startDate, endDate]);

  useEffect(() => {
    void load();
  }, [load]);

  function handleApply(e: FormEvent) {
    e.preventDefault();
    setPage(1);
    setReloadKey((k) => k + 1);
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Audit Trail</h1>

      {error && <ErrorAlert message={error} />}

      <form
        onSubmit={handleApply}
        className="flex flex-wrap gap-2 rounded-lg bg-white p-3 shadow"
      >
        <select
          value={action}
          onChange={(e) => setAction(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">Semua aksi</option>
          {ACTIONS.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
        <select
          value={entityType}
          onChange={(e) => setEntityType(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">Semua entitas</option>
          {ENTITY_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
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
      </form>

      {loading ? (
        <Spinner />
      ) : !data || data.items.length === 0 ? (
        <EmptyState message="Belum ada log pada filter ini." />
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg bg-white shadow">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-gray-500">
                  <th className="px-4 py-3">Waktu</th>
                  <th className="px-4 py-3">Pengguna</th>
                  <th className="px-4 py-3">Aksi</th>
                  <th className="px-4 py-3">Entitas</th>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Detail</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((log) => (
                  <tr key={log.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      {formatDateTime(log.created_at)}
                    </td>
                    <td className="px-4 py-3">{log.username ?? "—"}</td>
                    <td className="px-4 py-3">
                      <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">
                        {log.action}
                      </code>
                    </td>
                    <td className="px-4 py-3">{log.entity_type}</td>
                    <td className="px-4 py-3">
                      {log.entity_id !== null ? log.entity_id : "—"}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">
                      <code>
                        {log.details ? JSON.stringify(log.details) : "—"}
                      </code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>
              Halaman {data.page} dari{" "}
              {Math.max(1, Math.ceil(data.total / PAGE_SIZE))} ({data.total}{" "}
              log)
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
    </div>
  );
}