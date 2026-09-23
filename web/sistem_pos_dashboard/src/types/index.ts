export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserMe {
  id: number;
  role_id: number;
  username: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  role: string;
}

export type PaymentMethod = "CASH" | "QRIS" | "TRANSFER";
export type TransactionStatus = "PENDING" | "PAID" | "CANCELLED";

export interface Category {
  id: number;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: number;
  category_id: number;
  name: string;
  description: string | null;
  sku: string | null;
  price: number;
  image_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductList {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
}

export interface TransactionItem {
  id: number;
  product_id: number;
  product_name: string;
  price: number;
  quantity: number;
  subtotal: number;
  note: string | null;
}

export interface Payment {
  id: number;
  method: string;
  amount: number;
  change_amount: number;
}

export interface Transaction {
  id: number;
  invoice_number: string;
  cashier_id: number;
  subtotal: number;
  discount: number;
  total: number;
  payment_method: string;
  paid_amount: number;
  change_amount: number;
  status: TransactionStatus;
  created_at: string;
  items: TransactionItem[];
  payment: Payment | null;
}

export interface TransactionList {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
}

export interface TransactionRequestItem {
  product_id: number;
  quantity: number;
  note?: string | null;
}

export interface TransactionCreateRequest {
  items: TransactionRequestItem[];
  payment_method: PaymentMethod;
  paid_amount: number;
  discount: number;
  local_ref?: string;
  created_at_local?: string;
}

export interface SalesPoint {
  period: string;
  sales_total: number;
  transaction_count: number;
}

export interface BestSellerItem {
  product_name: string;
  quantity: number;
  revenue: number;
}

export interface BestSellerList {
  items: BestSellerItem[];
}

export interface DashboardSummary {
  start_date: string;
  end_date: string;
  sales_total: number;
  transaction_count: number;
  item_count: number;
  active_products: number;
  best_seller: BestSellerItem | null;
}
export interface StoreProfile {
  id: number;
  store_name: string;
  address: string | null;
  phone: string | null;
  footer: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: number;
  user_id: number | null;
  username: string | null;
  action: string;
  entity_type: string;
  entity_id: number | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogList {
  items: AuditLog[];
  total: number;
  page: number;
  page_size: number;
}
