import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";

import {
  EmptyState,
  ErrorAlert,
  Modal,
  Spinner,
} from "../components/ui";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import {
  createUser,
  fetchUsers,
  updateUser,
} from "../services/users";
import type { UserMe } from "../types";
import { formatDateTime } from "../utils/format";

const PAGE_SIZE = 10;
const EMPTY_FORM = {
  username: "",
  password: "",
  full_name: "",
  role: "KASIR" as "OWNER" | "KASIR",
};

export default function UsersPage() {
  const [users, setUsers] = useState<UserMe[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const debouncedQ = useDebouncedValue(q);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const seqRef = useRef(0);

  const [modalOpen, setModalOpen] = useState(false);
  const [editUser, setEditUser] = useState<UserMe | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const seq = ++seqRef.current;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchUsers({
        q: debouncedQ || undefined,
        page,
        page_size: PAGE_SIZE,
      });
      if (seq === seqRef.current) {
        setUsers(res.items);
        setTotal(res.total);
        // Halaman terakhir kosong (item terakhir baru saja dihapus): mundur
        // satu halaman agar pengguna tidak terjebak di daftar kosong.
        if (res.items.length === 0 && page > 1) {
          setPage((x) => Math.max(1, x - 1));
        }
      }
    } catch (err) {
      if (seq === seqRef.current) {
        console.error(err);
        setError("Gagal memuat daftar pengguna.");
      }
    } finally {
      if (seq === seqRef.current) setLoading(false);
    }
  }, [debouncedQ, page]);

  useEffect(() => {
    setPage(1);
  }, [debouncedQ]);

  useEffect(() => {
    void load();
  }, [load]);

  function openCreate() {
    setEditUser(null);
    setForm(EMPTY_FORM);
    setModalOpen(true);
  }

  function openEdit(u: UserMe) {
    setEditUser(u);
    setForm({
      username: u.username,
      password: "",
      full_name: u.full_name,
      role: u.role === "OWNER" ? "OWNER" : "KASIR",
    });
    setModalOpen(true);
  }

  function closeModal() {
    setModalOpen(false);
    setEditUser(null);
    setForm(EMPTY_FORM);
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    if (saving) return;
    if (!form.full_name.trim()) return;
    if (!editUser) {
      if (!form.username.trim() || form.password.length < 6) return;
    }
    setSaving(true);
    setError(null);
    try {
      if (editUser) {
        const payload: {
          full_name: string;
          role: "OWNER" | "KASIR";
          is_active: boolean;
          password?: string;
        } = {
          full_name: form.full_name.trim(),
          role: form.role,
          is_active: editUser.is_active,
        };
        if (form.password) payload.password = form.password;
        await updateUser(editUser.id, payload);
      } else {
        await createUser({
          username: form.username.trim(),
          password: form.password,
          full_name: form.full_name.trim(),
          role: form.role,
        });
      }
      closeModal();
      await load();
    } catch (err) {
      console.error(err);
      setError("Gagal menyimpan pengguna (username duplikat / role tidak valid).");
    } finally {
      setSaving(false);
    }
  }

  async function handleToggleActive(u: UserMe) {
    setSaving(true);
    setError(null);
    try {
      await updateUser(u.id, { is_active: !u.is_active });
      await load();
    } catch (err) {
      console.error(err);
      setError("Gagal mengubah status (harus selalu ada OWNER aktif).");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-800">Pengguna</h1>
        <div className="flex gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Cari pengguna..."
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
          />
          <button
            onClick={openCreate}
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
          >
            + Tambah Pengguna
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} />}

      {loading ? (
        <Spinner />
      ) : users.length === 0 ? (
        <EmptyState message="Belum ada pengguna." />
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg bg-white shadow">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-gray-500">
                  <th className="px-4 py-3">Nama</th>
                  <th className="px-4 py-3">Username</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Dibuat</th>
                  <th className="px-4 py-3 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{u.full_name}</td>
                    <td className="px-4 py-3 text-gray-500">{u.username}</td>
                    <td className="px-4 py-3">
                      {u.role === "OWNER" ? (
                        <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs text-indigo-700">
                          OWNER
                        </span>
                      ) : (
                        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700">
                          KASIR
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {u.is_active ? (
                        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700">
                          Aktif
                        </span>
                      ) : (
                        <span className="rounded-full bg-gray-200 px-2 py-0.5 text-xs text-gray-600">
                          Nonaktif
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {formatDateTime(u.created_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => openEdit(u)}
                        className="mr-3 text-emerald-700 hover:underline"
                      >
                        Ubah
                      </button>
                      <button
                        onClick={() => handleToggleActive(u)}
                        disabled={saving}
                        className={`${
                          u.is_active
                            ? "text-red-600"
                            : "text-emerald-700"
                        } hover:underline disabled:opacity-40`}
                      >
                        {u.is_active ? "Nonaktifkan" : "Aktifkan"}
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
              {total} pengguna)
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
        title={editUser ? `Ubah ${editUser.username}` : "Tambah Pengguna"}
        onClose={closeModal}
      >
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Nama lengkap *
            </label>
            <input
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              required
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-emerald-500 focus:outline-none"
            />
          </div>
          {!editUser && (
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Username *
              </label>
              <input
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                required
                pattern="[A-Za-z0-9_.\-]+"
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-emerald-500 focus:outline-none"
              />
            </div>
          )}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              {editUser ? "Password baru (kosongkan jika tidak diubah)" : "Password *"}
            </label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              minLength={editUser ? undefined : 6}
              required={!editUser}
              autoComplete="new-password"
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-emerald-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Role
            </label>
            <select
              value={form.role}
              onChange={(e) =>
                setForm({
                  ...form,
                  role: e.target.value as "OWNER" | "KASIR",
                })
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2"
            >
              <option value="KASIR">Kasir</option>
              <option value="OWNER">Owner</option>
            </select>
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
    </div>
  );
}