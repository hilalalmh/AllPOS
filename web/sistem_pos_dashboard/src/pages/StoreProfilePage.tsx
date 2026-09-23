import { useEffect, useState } from "react";

import { useStoreProfileStore } from "../stores/storeProfileStore";

const FIELDS: { name: string; label: string }[] = [
  { name: "store_name", label: "Nama Toko" },
  { name: "address", label: "Alamat" },
  { name: "phone", label: "Telepon" },
  { name: "footer", label: "Footer Struk" },
];

export default function StoreProfilePage() {
  const profile = useStoreProfileStore((s) => s.profile);
  const loading = useStoreProfileStore((s) => s.loading);
  const error = useStoreProfileStore((s) => s.error);
  const load = useStoreProfileStore((s) => s.load);
  const save = useStoreProfileStore((s) => s.save);

  const [form, setForm] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (profile) {
      setForm({
        store_name: profile.store_name,
        address: profile.address ?? "",
        phone: profile.phone ?? "",
        footer: profile.footer,
      });
    }
  }, [profile]);

  if (loading && !profile) {
    return <p className="text-sm text-gray-500">Memuat profil toko...</p>;
  }

  function updateField(name: string, value: string) {
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMsg(null);
    try {
      await save({
        store_name: form.store_name,
        address: form.address || null,
        phone: form.phone || null,
        footer: form.footer,
      });
      setMsg("Profil toko berhasil disimpan.");
    } catch (err) {
      setMsg(`Gagal menyimpan: ${(err as Error).message}`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="mb-4 text-xl font-semibold">Profil Toko</h1>
      <p className="mb-4 text-sm text-gray-600">
        Nama & alamat dipakai di header struk; footer dipakai di akhir struk
        kasir.
      </p>

      {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
      {msg && <p className="mb-3 text-sm text-emerald-700">{msg}</p>}

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-lg bg-white p-5 shadow"
      >
        {FIELDS.map((field) => (
          <label key={field.name} className="block">
            <span className="mb-1 block text-sm font-medium">{field.label}</span>
            <input
              type="text"
              value={form[field.name] ?? ""}
              onChange={(e) => updateField(field.name, e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            />
          </label>
        ))}
        <button
          type="submit"
          disabled={saving || loading}
          className="rounded-md bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {saving ? "Menyimpan..." : "Simpan Profil"}
        </button>
      </form>
    </div>
  );
}