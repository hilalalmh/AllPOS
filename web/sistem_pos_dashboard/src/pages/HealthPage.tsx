import { useEffect, useState } from "react";

import { fetchHealth, HealthResponse } from "../services/health";

type State =
  | { kind: "loading" }
  | { kind: "success"; data: HealthResponse }
  | { kind: "error"; message: string };

export default function HealthPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    fetchHealth()
      .then((data) => {
        if (!cancelled) setState({ kind: "success", data });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message =
            err instanceof Error ? err.message : "Unknown error";
          setState({ kind: "error", message });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.kind === "loading") {
    return <p className="text-gray-600">Checking API & database...</p>;
  }

  if (state.kind === "error") {
    return (
      <div className="rounded border border-red-300 bg-red-50 p-4 text-red-700">
        <p className="font-semibold">Gagal terhubung ke API</p>
        <p className="text-sm">{state.message}</p>
      </div>
    );
  }

  const { data } = state;
  const allOk = data.status === "ok" && data.database === "ok";

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Health Check</h1>
      <div
        className={`inline-flex items-center gap-2 rounded px-3 py-1 text-sm font-semibold text-white ${
          allOk ? "bg-emerald-600" : "bg-red-600"
        }`}
      >
        {allOk ? "SEMUA OK" : "MASALAH"}
      </div>
      <pre className="rounded border bg-white p-4 text-sm text-gray-800">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}