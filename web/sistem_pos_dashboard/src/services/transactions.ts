import { apiClient } from "./api";
import type {
  Transaction,
  TransactionCreateRequest,
  TransactionList,
} from "../types";

export interface TransactionQuery {
  q?: string;
  cashier_id?: number;
  payment_method?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export async function fetchTransactions(
  params: TransactionQuery
): Promise<TransactionList> {
  const { data } = await apiClient.get<TransactionList>("/transactions", {
    params,
  });
  return data;
}

export async function fetchTransaction(id: number): Promise<Transaction> {
  const { data } = await apiClient.get<Transaction>(`/transactions/${id}`);
  return data;
}

export async function createTransaction(
  payload: TransactionCreateRequest
): Promise<Transaction> {
  const { data } = await apiClient.post<Transaction>("/transactions", payload);
  return data;
}

export async function cancelTransaction(id: number): Promise<Transaction> {
  const { data } = await apiClient.post<Transaction>(`/transactions/${id}/cancel`);
  return data;
}