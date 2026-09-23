import { apiClient } from "./api";
import type { AuditLogList } from "../types";

export interface AuditLogQuery {
  action?: string;
  entity_type?: string;
  user_id?: number;
  start_date?: string;
  end_date?: string;
  q?: string;
  page?: number;
  page_size?: number;
}

export async function fetchAuditLogs(
  params: AuditLogQuery
): Promise<AuditLogList> {
  const { data } = await apiClient.get<AuditLogList>("/audit-logs", {
    params,
  });
  return data;
}

export async function downloadReport(
  format: "csv" | "pdf",
  params: {
    start_date?: string;
    end_date?: string;
    payment_method?: string;
    status?: string;
  }
): Promise<void> {
  const { data } = await apiClient.get(`/reports/transactions.${format}`, {
    params,
    responseType: format === "csv" ? "text" : "blob",
  });

  if (format === "csv") {
    const blob = new Blob(["\uFEFF", data as string], {
      type: "text/csv;charset=utf-8",
    });
    triggerDownload(blob, "transactions.csv");
    return;
  }

  triggerDownload(data as Blob, "transactions.pdf");
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}