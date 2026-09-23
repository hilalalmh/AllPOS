import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react";

import {
  EmptyState,
  ErrorAlert,
  Modal,
  Spinner,
} from "../components/ui";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { fetchCategories } from "../services/categories";
import {
  createProduct,
  deleteProduct,
  fetchProducts,
  updateProduct,
  type ProductInput,
} from "../services/products";
import { useAuthStore } from "../stores/authStore";
import type { Category, Product } from "../types";
import { formatRupiah } from "../utils/format";

const PAGE_SIZE = 10;
const EMPTY_FORM: ProductInput = {
  category_id: 0,
  name: "",
  description: "",
  sku: "",
  price: 0,
  is_active: true,
};

export default function ProductsPage() {
  const user = useAuthStore((s) => s.user);
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [includeInactive, setIncludeInactive] = useState(false);
  const debouncedQ = useDebouncedValue(q);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categoriesError, setCategoriesError] = useState<string | null>(null);
  const seqRef = useRef(0);

  const [editId, setEditId] = useState<number | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<ProductInput>(EMPTY_FORM);
  const [image, setImage] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<Product | null>(null);

  const load = useCallback(async () => {
    const seq = ++seqRef.current;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchProducts({
        q: debouncedQ || undefined,
        include_inactive: includeInactive || undefined,
        page,
        page_size: PAGE_SIZE,
      });
      if (seq === seqRef.current) {
        setProducts(res.items);
        setTotal(res.total);
      }
    } catch (err) {
      if (seq === seqRef.current) {
        console.error(err);
        setError("Gagal memuat produk.");
      }
    } finally {
      if (seq === seqRef.current) setLoading(false);
    }
  }, [debouncedQ, page, includeInactive]);

  useEffect(() => {
    setPage(1);
  }, [debouncedQ, includeInactive]);

  useEffect(() => {
    void load();
    // Error memuat kategori tidak boleh ditelan diam-diam: tanpa daftar
    // kategori, produk tidak bisa dikategorikan/dibuat.
    void fetchCategories()
      .then((cs) => {
        setCategories(cs);
        setCategoriesError(null);
      })
      .catch((err) => {
        console.error(err);
        setCategoriesError("Gagal memuat daftar kategori.");
      });
  }, [load]);

  if (user?.role !== "OWNER") {
    return <div className="text-red-600">Akses ditolak: khusus owner.</div>;
  }

  function openCreate() {
    setEditId(null);
    setForm({ ...EMPTY_FORM, category_id: categories[0]?.id ?? 0 });
    setImage(null);
    setModalOpen(true);
  }

  function openEdit(p: Product) {
    setEditId(p.id);
    setForm({
      category_id: p.category_id,
      name: p.name,
      description: p.description ?? "",
      sku: p.sku ?? "",
      price: p.price,
      is_active: p.is_active,
    });
    setImage(null);
    setModalOpen(true);
  }

  function closeModal() {
    setModalOpen(false);
    setEditId(null);
    setForm(EMPTY_FORM);
    setImage(null);
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    if (!form.name.trim() || form.category_id === 0 || form.price <= 0) return;
    setSaving(true);
    setError(null);
    try {
      const payload: ProductInput = {
        ...form,
        name: form.name.trim(),
        price: Number(form.price),
      };
      if (editId) {
        await updateProduct(editId, payload);
      } else {
        await createProduct(payload, image);
      }
      setForm(EMPTY_FORM);
      setEditId(null);
      setImage(null);
      setModalOpen(false);
      await load();
    } catch (err) {
      console.error(err);
      setError("Gagal menyimpan produk (check: SKU unik, kategori aktif).");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirmDelete) return;
    setSaving(true);
    setError(null);
    try {
      await deleteProduct(confirmDelete.id);
      setConfirmDelete(null);
      await load();
    } catch (err) {
      console.error(err);
      setError("Gagal menghapus produk (masih dipakai transaksi?).");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-800">Produk</h1>
        <div className="flex gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Cari produk..."
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
          />
          <label className="flex cursor-pointer items-center gap-1.5 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
            />
            Tampilkan nonaktif
          </label>
          <button
            onClick={openCreate}
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
          >
            + Tambah Produk
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} />}
      {categoriesError && <ErrorAlert message={categoriesError} />}

      {loading ? (
        <Spinner />
      ) : products.length === 0 ? (
        <EmptyState message="Belum ada produk." />
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg bg-white shadow">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-gray-500">
                  <th className="px-4 py-3">Nama</th>
                  <th className="px-4 py-3">SKU</th>
                  <th className="px-4 py-3">Kategori</th>
                  <th className="px-4 py-3 text-right">Harga</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">
                      <div className="flex items-center gap-3">
                        {p.image_url && (
                          <img
                            src={p.image_url}
                            alt={p.name}
                            className="h-9 w-9 rounded object-cover"
                          />
                        )}
                        {p.name}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{p.sku ?? "-"}</td>
                    <td className="px-4 py-3">
                      {categories.find((c) => c.id === p.category_id)?.name ??
                        "-"}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold">
                      {formatRupiah(p.price)}
                    </td>
                    <td className="px-4 py-3">
                      {p.is_active ? (
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
                        onClick={() => openEdit(p)}
                        className="mr-3 text-emerald-700 hover:underline"
                      >
                        Ubah
                      </button>
                      <button
                        onClick={() => setConfirmDelete(p)}
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

          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>
              Halaman {page} dari {Math.max(1, Math.ceil(total / PAGE_SIZE))} (
              {total} produk)
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((x) => Math.max(1, x - 1))}
                disabled={page <= 1}
                className="rounded-md border border-gray-300 px-3 py-1 disabled:opacity-40"
              >
                Sebelumnya
              </button>
              <button
                onClick={() => setPage((x) => x + 1)}
                disabled={page * PAGE_SIZE >= total}
                className="rounded-md border border-gray-300 px-3 py-1 disabled:opacity-40"
              >
                Berikutnya
              </button>
            </div>
          </div>
        </>
      )}

      <Modal
        open={modalOpen}
        title={editId ? "Ubah Produk" : "Tambah Produk"}
        onClose={closeModal}
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Nama *
            </label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-emerald-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Kategori *
            </label>
            <select
              value={form.category_id}
              onChange={(e) =>
                setForm({ ...form, category_id: Number(e.target.value) })
              }
              required
              className="w-full rounded-md border border-gray-300 px-3 py-2"
            >
              <option value={0} disabled>
                Pilih kategori...
              </option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Harga *
              </label>
              <input
                type="number"
                min={1}
                step="any"
                value={form.price}
                onChange={(e) =>
                  setForm({ ...form, price: Number(e.target.value) })
                }
                required
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                SKU
              </label>
              <input
                value={form.sku ?? ""}
                onChange={(e) => setForm({ ...form, sku: e.target.value })}
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Deskripsi
            </label>
            <textarea
              value={form.description ?? ""}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              rows={2}
              className="w-full rounded-md border border-gray-300 px-3 py-2"
            />
          </div>
          {!editId && (
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Gambar
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setImage(e.target.files?.[0] ?? null)
                }
                className="w-full text-sm"
              />
            </div>
          )}
          <div>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) =>
                  setForm({ ...form, is_active: e.target.checked })
                }
              />
              Produk aktif
            </label>
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
        title="Hapus Produk"
        onClose={() => setConfirmDelete(null)}
      >
        <p className="text-sm text-gray-600">
          Hapus produk <b>{confirmDelete?.name}</b>? Aksi tidak bisa dibatalkan.
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