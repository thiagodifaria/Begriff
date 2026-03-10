const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

function toFormUrlEncoded(data) {
  return new URLSearchParams(data).toString();
}

async function request(path, { method = "GET", token, body, headers = {} } = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers
    },
    body: body ? JSON.stringify(body) : undefined
  });

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      message = errorBody.detail || errorBody.message || message;
    } catch {
      // ignore parse errors
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export async function login(email, password) {
  const response = await fetch(`${API_BASE_URL}/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: toFormUrlEncoded({ username: email, password })
  });

  if (!response.ok) {
    throw new Error("Credenciais invalidas.");
  }
  return response.json();
}

export function getCurrentUser(token) {
  return request("/users/me", { token });
}

export function getAnalysisHistory(token) {
  return request("/analysis/", { token });
}

export function getBankingAnalysisHistory(token) {
  return request("/banking/analysis/history", { token });
}

export function connectBankAccount(token, idBanco) {
  return request("/banking/account", {
    method: "POST",
    token,
    body: { id_banco: idBanco }
  });
}

export function runBankingAnalysis(token) {
  return request("/banking/analysis", { method: "POST", token });
}

export function getUiSettings(token) {
  return request("/ui/settings", { token });
}

export function saveUiSettings(token, settings) {
  return request("/ui/settings", { method: "PUT", token, body: { settings } });
}

export function listReports(token) {
  return request("/ui/reports", { token });
}

export function generateReport(token, payload = {}) {
  return request("/ui/reports/generate", { method: "POST", token, body: payload });
}

export async function downloadReport(token, reportId) {
  const response = await fetch(`${API_BASE_URL}/ui/reports/${reportId}/download`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) {
    throw new Error("Falha ao baixar relatorio.");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `report_${reportId}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

export async function exportTransactionsCsv(token) {
  const response = await fetch(`${API_BASE_URL}/ui/transactions/export.csv`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) {
    throw new Error("Falha ao exportar CSV.");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "transactions_export.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export function verifyAuditHash(token, hash) {
  return request("/ui/audit/verify", { method: "POST", token, body: { hash } });
}

export function listFilteredTransactions(token, filters = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") {
      searchParams.set(k, String(v));
    }
  });
  const qs = searchParams.toString();
  return request(`/ui/transactions${qs ? `?${qs}` : ""}`, { token });
}

export function listReportSchedules(token) {
  return request("/ui/reports/schedules", { token });
}

export function createReportSchedule(token, payload) {
  return request("/ui/reports/schedules", { method: "POST", token, body: payload });
}

export function simulateBackendData(token, params = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") {
      searchParams.set(k, String(v));
    }
  });
  const qs = searchParams.toString();
  return request(`/ui/data/simulate${qs ? `?${qs}` : ""}`, { method: "POST", token });
}

export function resetUserData(token) {
  return request("/ui/data/reset", { method: "DELETE", token });
}
