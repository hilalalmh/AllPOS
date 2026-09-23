import { useCallback, useEffect, useState, type FormEvent } from "react";

import { EmptyState, ErrorAlert, Modal, Spinner } from "../components/ui";
import {
  createCategory,
  deleteCategory,
  fetchCategories,
  updateCategory,
} from "../services/categories";
import { useAuthStore } from "../stores/authStore";
import type { Category } from "../types";

export default function CategoriesPage() {
  const user = useAuthStore((s) => s.user);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [edit, setEdit] = useState<{ id?: number; name: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<Category | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setCategories(await fetchCategories());
    } catch (err) {
      console.error(err);
      setError("Gagal memuat kategori.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (user?.role !== "OWNER") {
    return <div className="text-red-600">Akses ditolak: khusus owner.</div>;
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    if (saving) return;
    if (!edit || !edit.name.trim()) return;
    setSaving(true);
    setError(null);
    try {
      if (edit.id) {
        await updateCategory(edit.id, { name: edit.name.trim() });
      } else {
        await createCategory({ name: edit.name.trim() });
      }
      setEdit(null);
      await load();
    } catch (err) {
      console.error(err);
      setError("Gagal menyimpan kategori.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirmDelete || saving) return;
    setSaving(true);
    setError(null);
    try {
      await deleteCategory(confirmDelete.id);
      setConfirmDelete(null);
      await load();
    } catch (err) {
      console.error(err);
      setError("Gagal menghapus kategori (masih dipakai produk? Nama duplikat?).");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Kategori</h1>
        <button
          onClick={() => setEdit({ name: "" })}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          + Tambah Kategori
        </button>
      </div>

      {error && <ErrorAlert message={error} />}

      {loading ? (
        <Spinner />
      ) : categories.length === 0 ? (
        <EmptyState message="Belum ada kategori." />
      ) : (
        <div className="overflow-x-auto rounded-lg bg-white shadow">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 text-left text-gray-500">
                <th className="px-4 py-3">Nama</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {categories.map((c) => (
                <tr key={c.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{c.name}</td>
                  <td className="px-4 py-3">
                    {c.is_active ? (
                      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700">
                        Aktif
                      </span>
                    ) : (
                      <span className="rounded-full bg-gray-200 px-2 py-0.5 text-xs text-gray-600">
                        Nonaktif
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setEdit({ id: c.id, name: c.name })}
                      className="mr-3 text-emerald-700 hover:underline"
                    >
                      Ubah
                    </button>
                    <button
                      onClick={() => setConfirmDelete(c)}
                      className="text-red-600 hover:underline"
                    >
                      Hapus
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={edit !== null}
        title={edit?.id ? "Ubah Kategori" : "Tambah Kategori"}
        onClose={() => setEdit(null)}
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Nama
            </label>
            <input
              value={edit?.name ?? ""}
              onChange={(e) =>
                setEdit((prev) => (prev ? { ...prev, name: e.target.value } : prev))
              }
              autoFocus
              required
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-emerald-500 focus:outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={saving}
            className="w-full rounded-md bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {saving ? "Menyimpan..." : "Simpan"}
          </button>
        </form>
      </Modal>

      <Modal
        open={confirmDelete !== null}
        title="Hapus Kategori"
        onClose={() => setConfirmDelete(null)}
      >
        <p className="text-sm text-gray-600">
          Hapus kategori <b>{confirmDelete?.name}</b>? Aksi tidak bisa dibatalkan.
        </p>
        <div className="mt-4 flex gap-3">
          <button
            onClick={() => setConfirmDelete(null)}
            className="flex-1 rounded-md border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50"
          >
            Batal
          </button>
          <button
            onClick={handleDelete}
            disabled={saving}
            className="flex-1 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
          >
            {saving ? "Menghapus..." : "Hapus"}
          </button>
        </div>
      </Modal>
    </div>
  );
}