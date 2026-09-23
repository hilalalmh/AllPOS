import { useEffect, useMemo, useRef, useState } from "react";

import { ErrorAlert, Modal, Spinner } from "../components/ui";
import { fetchCategories } from "../services/categories";
import { fetchProducts } from "../services/products";
import { createTransaction } from "../services/transactions";
import { useAuthStore } from "../stores/authStore";
import { useStoreProfileStore } from "../stores/storeProfileStore";
import type {
  Category,
  PaymentMethod,
  Product,
  Transaction,
} from "../types";
import { formatDateTime, formatMoney, formatRupiah } from "../utils/format";
import { randomUuid } from "../utils/uuid";

interface CartLine {
  product: Product;
  quantity: number;
}

const PAYMENT_LABELS: Record<PaymentMethod, string> = {
  CASH: "Tunai",
  QRIS: "QRIS",
  TRANSFER: "Transfer",
};

// Bulatkan ke sen agar presisi float (mis. 5.050000000000001) tidak membuat
// klien mengirim nilai 0.001 lebih kecil/gemuk dari yang divisualisasikan.
function round2(n: number): number {
  return Math.round((n + Number.EPSILON) * 100) / 100;
}

export default function PosPage() {
  const user = useAuthStore((s) => s.user);
  const storeProfileLoad = useStoreProfileStore((s) => s.load);
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [search, setSearch] = useState("");
  const [catId, setCatId] = useState<number | "">("");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [method, setMethod] = useState<PaymentMethod>("CASH");
  const [discount, setDiscount] = useState("");
  const [paid, setPaid] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<Transaction | null>(null);

  const cartKeyRef = useRef("");
  const clientRefRef = useRef<string | null>(null);

  // Idempotensi: buat local_ref tetap utuh selama isi keranjang sama,
  // agar klien yang retry tidak menciptakan transaksi ganda.
  useEffect(() => {
    const key = JSON.stringify(
      cart.map((l) => [l.product.id, l.quantity, l.product.price])
    );
    if (key !== cartKeyRef.current) {
      cartKeyRef.current = key;
      clientRefRef.current = randomUuid();
    }
  }, [cart]);

  useEffect(() => {
    let cancelled = false;
    storeProfileLoad();
    (async function loadAll() {
      const pageSize = 100;
      const all: Product[] = [];
      let page = 1;
      try {
        while (true) {
          const res = await fetchProducts({ page, page_size: pageSize });
          all.push(...res.items);
          if (page * pageSize >= res.total || res.items.length === 0) {
            break;
          }
          page += 1;
        }
        if (cancelled) return;
        setProducts(all);
        setCategories(await fetchCategories());
      } catch (err) {
        if (cancelled) return;
        setError("Gagal memuat produk.");
        console.error(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(
    () =>
      products.filter((p) => {
        if (catId !== "" && p.category_id !== catId) return false;
        if (!search) return true;
        return p.name.toLowerCase().includes(search.toLowerCase());
      }),
    [products, search, catId]
  );

  const subtotal = useMemo(
    () => cart.reduce((sum, line) => sum + line.product.price * line.quantity, 0),
    [cart]
  );
  const discountValue = round2(Number(discount) || 0);
  const total = Math.max(round2(subtotal - discountValue), 0);
  const paidValue = round2(Number(paid) || 0);
  const change = round2(paidValue - total);

  function addToCart(product: Product) {
    setCart((prev) => {
      const existing = prev.find((l) => l.product.id === product.id);
      if (existing) {
        return prev.map((l) =>
          l.product.id === product.id
            ? { ...l, quantity: l.quantity + 1 }
            : l
        );
      }
      return [...prev, { product, quantity: 1 }];
    });
  }

  function setQty(productId: number, quantity: number) {
    if (quantity <= 0) {
      setCart((prev) => prev.filter((l) => l.product.id !== productId));
      return;
    }
    setCart((prev) =>
      prev.map((l) =>
        l.product.id === productId ? { ...l, quantity } : l
      )
    );
  }

  function canSubmit() {
    return (
      cart.length > 0 &&
      total > 0 &&
      paidValue >= total &&
      discountValue <= subtotal &&
      !submitting
    );
  }

  async function handleCheckout() {
    setSubmitting(true);
    setError(null);
    try {
      const tx = await createTransaction({
        items: cart.map((l) => ({
          product_id: l.product.id,
          quantity: l.quantity,
          note: null,
        })),
        payment_method: method,
        paid_amount: paidValue,
        discount: discountValue,
        local_ref: clientRefRef.current ?? undefined,
      });
      clientRefRef.current = null;
      setCart([]);
      setPaid("");
      setDiscount("");
      setResult(tx);
    } catch (err) {
      console.error(err);
      setError("Transaksi gagal diproses.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <Spinner />;

  return (
    <>
      <div className="space-y-4 print:hidden">
        <h1 className="text-2xl font-bold text-gray-800">Kasir &amp; Bayar</h1>

      {error && <ErrorAlert message={error} />}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Produk */}
        <div className="lg:col-span-2">
          <div className="mb-3 flex flex-wrap gap-2">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Cari produk..."
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            />
            <select
              value={catId}
              onChange={(e) =>
                setCatId(e.target.value === "" ? "" : Number(e.target.value))
              }
              className="rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">Semua kategori</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {filtered.length === 0 ? (
            <div className="rounded-md border border-dashed border-gray-300 py-10 text-center text-sm text-gray-500">
              Tidak ada produk.
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {filtered.map((p) => (
                <button
                  key={p.id}
                  onClick={() => addToCart(p)}
                  className="rounded-lg border border-gray-200 bg-white p-3 text-left shadow-sm transition hover:border-emerald-500 hover:shadow"
                >
                  <p className="truncate font-medium text-gray-800">
                    {p.name}
                  </p>
                  <p className="mt-1 text-sm font-semibold text-emerald-700">
                    {formatRupiah(p.price)}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Cart */}
        <div className="space-y-4">
          <div className="rounded-lg bg-white p-4 shadow">
            <h2 className="mb-3 font-semibold text-gray-700">
              Keranjang ({cart.reduce((s, l) => s + l.quantity, 0)})
            </h2>
            {cart.length === 0 ? (
              <p className="py-4 text-center text-sm text-gray-400">
                Keranjang kosong.
              </p>
            ) : (
              <ul className="max-h-64 space-y-2 overflow-y-auto">
                {cart.map((l) => (
                  <li
                    key={l.product.id}
                    className="flex items-center justify-between gap-2 text-sm"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-medium">{l.product.name}</p>
                      <p className="text-gray-500">
                        {formatRupiah(l.product.price)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setQty(l.product.id, l.quantity - 1)}
                        className="h-7 w-7 rounded bg-gray-100 hover:bg-gray-200"
                      >
                        &minus;
                      </button>
                      <span className="w-6 text-center">{l.quantity}</span>
                      <button
                        onClick={() => setQty(l.product.id, l.quantity + 1)}
                        className="h-7 w-7 rounded bg-gray-100 hover:bg-gray-200"
                      >
                        +
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            <div className="mt-4 space-y-2 border-t pt-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Subtotal</span>
                <span className="font-medium">{formatRupiah(subtotal)}</span>
              </div>
              <div className="flex items-center justify-between">
                <label className="text-gray-500">Diskon</label>
                <input
                  type="number"
                  min={0}
                  value={discount}
                  onChange={(e) => setDiscount(e.target.value)}
                  className="w-28 rounded border border-gray-300 px-2 py-1 text-right"
                  placeholder="0"
                />
              </div>
              <div className="flex justify-between text-base font-bold">
                <span>Total</span>
                <span>{formatRupiah(total)}</span>
              </div>
            </div>
          </div>

          <div className="rounded-lg bg-white p-4 shadow">
            <h2 className="mb-3 font-semibold text-gray-700">Pembayaran</h2>
            <div className="mb-3 flex gap-2">
              {(Object.keys(PAYMENT_LABELS) as PaymentMethod[]).map((m) => (
                <button
                  key={m}
                  onClick={() => setMethod(m)}
                  className={`flex-1 rounded-md border px-2 py-2 text-sm ${
                    method === m
                      ? "border-emerald-600 bg-emerald-50 font-medium text-emerald-700"
                      : "border-gray-300 text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  {PAYMENT_LABELS[m]}
                </button>
              ))}
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <label className="text-gray-500">Dibayar</label>
                <input
                  type="number"
                  min={0}
                  value={paid}
                  onChange={(e) => setPaid(e.target.value)}
                  className="w-32 rounded border border-gray-300 px-2 py-1 text-right"
                  placeholder="0"
                />
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Kembalian</span>
                <span
                  className={
                    change < 0 ? "font-medium text-red-600" : "font-medium"
                  }
                >
                  {change < 0
                    ? `Kurang ${formatRupiah(-change)}`
                    : formatRupiah(change)}
                </span>
              </div>
            </div>

            <button
              onClick={handleCheckout}
              disabled={!canSubmit()}
              className="mt-4 w-full rounded-md bg-emerald-600 px-4 py-2.5 font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? "Memproses..." : "Proses Pembayaran"}
            </button>
            {discountValue > subtotal && (
              <p className="mt-2 text-xs text-red-600">
                Diskon melebihi subtotal.
              </p>
            )}
          </div>
        </div>
      </div>

      {result && (
        <Modal
          open
          title="Transaksi Berhasil"
          onClose={() => setResult(null)}
        >
          <SuccessReceipt tx={result} cashier={user?.full_name ?? "-"} onPrint={() => window.print()} />
        </Modal>
      )}

      {result && <ReceiptPrintView tx={result} cashier={user?.full_name ?? "-"} />}
      </div>
    </>
  );
}

function SuccessReceipt({
  tx,
  cashier,
  onPrint,
}: {
  tx: Transaction;
  cashier: string;
  onPrint: () => void;
}) {
  return (
    <div>
      <div className="mb-4 rounded-md bg-emerald-50 px-4 py-3 text-center">
        <p className="font-semibold text-emerald-700">Pembayaran berhasil</p>
        <p className="text-sm text-emerald-600">{tx.invoice_number}</p>
        <p className="text-sm text-emerald-600">
          Kembalian: {formatRupiah(tx.change_amount)}
        </p>
      </div>
      <dl className="space-y-1.5 text-sm">
        <div className="flex justify-between">
          <dt className="text-gray-500">Kasir</dt>
          <dd>{cashier}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-500">Waktu</dt>
          <dd>{formatDateTime(tx.created_at)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-500">Metode</dt>
          <dd>{PAYMENT_LABELS[tx.payment_method as PaymentMethod] ?? tx.payment_method}</dd>
        </div>
      </dl>
      <button
        onClick={onPrint}
        className="mt-4 w-full rounded-md bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-700"
      >
        Cetak Struk
      </button>
    </div>
  );
}

export function ReceiptPrintView({ tx, cashier }: { tx: Transaction; cashier: string }) {
  return (
    <div className="print-area hidden">
      <ReceiptTicket tx={tx} cashier={cashier} />
    </div>
  );
}

export function ReceiptTicket({
  tx,
  cashier,
}: {
  tx: Transaction;
  cashier: string;
}) {
  const profile = useStoreProfileStore((s) => s.profile);
  const storeName = profile?.store_name || "SISTEM POS";
  const storeInfo = [profile?.address, profile?.phone]
    .filter(Boolean)
    .join(" • ");

  return (
    <div className="font-mono text-xs leading-tight" style={{ width: "58mm" }}>
      <p className="text-center font-bold">{storeName}</p>
      {storeInfo && <p className="text-center">{storeInfo}</p>}
      <p className="text-center">{formatDateTime(tx.created_at)}</p>
      <div className="my-1 border-t border-dashed" />
      <p>
        No: {tx.invoice_number}
        <br />
        Kasir: {cashier}
      </p>
      <div className="my-1 border-t border-dashed" />
      {tx.items.map((item) => (
        <p key={item.id}>
          {item.product_name}
          <br />
          {item.quantity} x {formatMoney(item.price)} ={" "}
          {formatMoney(item.subtotal)}
        </p>
      ))}
      <div className="my-1 border-t border-dashed" />
      <p>Subtotal: {formatMoney(tx.subtotal)}</p>
      <p>Diskon: -{formatMoney(tx.discount)}</p>
      <p className="font-bold">TOTAL: {formatMoney(tx.total)}</p>
      <p>
        {PAYMENT_LABELS[tx.payment_method as PaymentMethod] ?? tx.payment_method}:
        {formatMoney(tx.paid_amount)}
      </p>
      <p>Kembalian: {formatMoney(tx.change_amount)}</p>
      <div className="my-1 border-t border-dashed" />
      <p className="text-center">{profile?.footer || "Terima kasih!"}</p>
    </div>
  );
}