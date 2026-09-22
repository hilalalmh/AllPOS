# Tujuan & Aturan Proyek — Sistem POS

Dokumen acuan utama. Baca ini dulu sebelum mengerjakan apa pun agar tidak menyimpang dari tujuan project dan tidak kehilangan progress.

## 1. Apa yang Dibangun

Sistem Point of Sale untuk coffee shop/kedai dengan 4 komponen utama:

1. **Mobile Kasir (Flutter)** — dipakai kasir di lapangan: login, pilih produk, checkout, cetak struk thermal (Bluetooth), cetak ulang.
2. **Web Dashboard (React + Vite)** — dipakai owner/manager: kelola produk & kategori, lihat & batalkan transaksi, statistik penjualan & menu terlaris, kasir & bayar dari browser.
3. **Backend (FastAPI)** — sumber kebenaran (source of truth) untuk data, harga, dan kalkulasi transaksi. REST JSON + Bearer JWT.
4. **Database (PostgreSQL)** — penyimpanan utama; SQLite lokal di Flutter hanyalah cadangan/offline.

## 2. Prinsip Utama (SLM Master Rules)

Aturan ini wajib selamanya dipatuhi:

1. **Backend adalah otoritas harga.** Klien (Flutter/React) TIDAK boleh mengirim harga final; harga transaksi diambil dari database. Klien hanya mengirim `product_id` + `quantity`. Semua kalkulasi subtotal/diskon/total/kembalian dihitung & disimpan backend.
2. **Invoice unik & otomatis.** Format `POS-YYYYMMDD-XXXX`, urut harian, unik (UNIQUE constraint), dengan retry bila race.
3. **Transaksi tidak pernah dihapus.** Hanya `CANCELLED` (status), item & payment tetap tersimpan utuh.
4. **Snapshot transaksi.** `product_name` + `price` disalin ke `transaction_items` saat transaksi dibuat — riwayat tidak berubah meski produk diubah nanti.
5. **Uang pakai NUMERIC(12,2)** di DB; dikirim sebagai float di API.
6. **Pagination wajib** untuk list (transaksi, produk). Parameter `page`/`page_size` konsisten.
7. **Cukup bukti, bukan klaim.** Setiap fase Selesai = teruji (pytest backend, widget test / lint build web + Flutter, dan verifikasi live API), bukan sekadar "kodenya jadi".
8. **Jangan commit secret.** Semua kredensial/token lewat `.env`, tidak pernah masuk git.

## 3. Fase Roadmap (Urut, Jangan Dilompati)

| Phase | Isi | Status |
|-------|-----|--------|
| 1 | Foundation: env, struktur, FastAPI+DB, Vite+proxy, Alembic, scripts | DONE |
| 2 | Authentication: users/roles, bcrypt, JWT access+refresh, RBAC, seed | DONE |
| 3 | Product: kategori/produk, CRUD, upload gambar, pagination | DONE |
| 4 | POS/Transaction: transaksi atomarik, invoice unik, payment, cancel, audit | DONE |
| 5 | Mobile Flutter + Printer: login, sesi, printer BT, struk, APK | DONE |
| 6 | Dashboard Web: login admin, bayar, transaksi, CRUD produk, statistik | DONE |
| 7 | Integrasi & Offline Mobile: cart/checkout Flutter, sinkronisasi SQLite offline | BERIKUTNYA |
| 8 | Fitur lanjut: profil toko, barcode/QR di struk, export laporan, deploy | TODO |

## 4. Target & Kualitas

- Semua alur di dashboard web & app kasir menggunakan **satu API yang sama** (tidak ada logika ganda).
- Printer gagal **tidak menghapus transaksi** — struk bisa dicetak ulang.
- Offline (PHASE 7): transaksi bisa diantrekan di SQLite lalu disinkronkan saat online.
- Dashboard statistik & struk bergantung data backend (bukan data lokal).

## 5. Cara Agar Progress Tidak Hilang

1. **Catat status terkini** di `docs/memory.md` (lingkungan, keputusan, gotcha, hasil verifikasi).
2. **Update roadmap** (`docs/roadmap.md`) segera saat fase selesai.
3. **Backup database** sebelum eksperimen besar — cara: `docs/setup.md#backup-&-restore`.
4. **Verifikasi selalu live** (jangan claim tanpa cek). Backend hidup di `:8000`, web di `:5173`.
5. Kalau ada keputusan teknis baru yang menyangkut seluruh sistem, tambahkan di `docs/memory.md`.

## 6. Akun Akses

| User | Password | Role |
|------|----------|------|
| `owner` | `admin123` | OWNER — akses penuh dashboard & tulis produk |
| `kasir1` / `kasir2` | `kasir123` | KASIR — bayar & transaksi miliknya |

Password seed owner diubah lewat `SEED_ADMIN_PASSWORD` di `.env` untuk produksi.