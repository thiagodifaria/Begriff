import { useEffect, useState } from "react";

import Login from "./components/Login";
import { useAuth } from "./hooks/useAuth";
import { useUiData } from "./hooks/useUiData";
import Layout from "./layout/Layout";
import {
  connectBankAccount,
  createReportSchedule,
  downloadReport,
  exportTransactionsCsv,
  generateReport,
  getUiSettings,
  listFilteredTransactions,
  listReports,
  listReportSchedules,
  resetUserData,
  runBankingAnalysis,
  saveUiSettings,
  simulateBackendData,
  verifyAuditHash
} from "./services/api";

function LoadingScreen() {
  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[#fafaf9]">
      <div className="text-xs font-mono text-gray-500">Carregando plataforma...</div>
    </div>
  );
}

export default function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");
  const auth = useAuth();
  const { uiData, loading: loadingData, error: dataError, reload } = useUiData(auth.token);
  const [uiSettings, setUiSettings] = useState({});
  const [reports, setReports] = useState([]);
  const [reportSchedules, setReportSchedules] = useState([]);
  const [filteredTransactions, setFilteredTransactions] = useState([]);
  const [toast, setToast] = useState("");

  async function handleSyncBank(idBanco) {
    if (!auth.token) return;
    await connectBankAccount(auth.token, idBanco);
    await runBankingAnalysis(auth.token);
    await reload();
    setToast("Sync bancario concluido.");
  }

  async function handleExportCsv() {
    if (!auth.token) return;
    await exportTransactionsCsv(auth.token);
    setToast("Exportacao CSV concluida.");
  }

  async function handleLoadFilteredTransactions(filters) {
    if (!auth.token) return;
    const rows = await listFilteredTransactions(auth.token, filters);
    setFilteredTransactions(rows || []);
  }

  async function handleLoadSettings() {
    if (!auth.token) return;
    const response = await getUiSettings(auth.token);
    setUiSettings(response.settings || {});
  }

  async function handleSaveSettings(nextSettings) {
    if (!auth.token) return;
    const response = await saveUiSettings(auth.token, nextSettings);
    setUiSettings(response.settings || nextSettings);
    setToast("Configuracoes salvas.");
  }

  async function handleLoadReports() {
    if (!auth.token) return;
    const response = await listReports(auth.token);
    setReports(response || []);
  }

  async function handleLoadSchedules() {
    if (!auth.token) return;
    const response = await listReportSchedules(auth.token);
    setReportSchedules(response || []);
  }

  async function handleGenerateReport(analysisId) {
    if (!auth.token) return;
    await generateReport(auth.token, { analysis_id: analysisId });
    await handleLoadReports();
    setToast("Relatorio gerado.");
  }

  async function handleDownloadReport(reportId) {
    if (!auth.token) return;
    await downloadReport(auth.token, reportId);
  }

  async function handleCreateSchedule(payload) {
    if (!auth.token) return;
    await createReportSchedule(auth.token, payload);
    await handleLoadSchedules();
    setToast("Agendamento salvo.");
  }

  async function handleSimulateData(params) {
    if (!auth.token) return;
    const result = await simulateBackendData(auth.token, params);
    await Promise.all([reload(), handleLoadReports(), handleLoadSchedules(), handleLoadFilteredTransactions({})]);
    setToast(result.message || "Simulacao concluida.");
  }

  async function handleResetData() {
    if (!auth.token) return;
    const result = await resetUserData(auth.token);
    setReports([]);
    setReportSchedules([]);
    setFilteredTransactions([]);
    await reload();
    setToast(result.message || "Dados resetados.");
  }

  async function handleVerifyAudit(hash) {
    if (!auth.token) return { verified: false };
    return verifyAuditHash(auth.token, hash);
  }

  useEffect(() => {
    if (!auth.isAuthenticated) return;
    handleLoadSettings();
    handleLoadReports();
    handleLoadSchedules();
    handleLoadFilteredTransactions({});
  }, [auth.isAuthenticated]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 2500);
    return () => clearTimeout(timer);
  }, [toast]);

  if (auth.loading) {
    return <LoadingScreen />;
  }

  if (!auth.isAuthenticated) {
    return <Login onLogin={auth.login} authError={auth.error} />;
  }

  return (
    <>
      <Layout
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        onLogout={() => {
          auth.logout();
          setCurrentPage("dashboard");
        }}
        uiData={uiData}
        filteredTransactions={filteredTransactions}
        reports={reports}
        reportSchedules={reportSchedules}
        uiSettings={uiSettings}
        user={auth.user}
        onSyncBank={handleSyncBank}
        onExportCsv={handleExportCsv}
        onLoadFilteredTransactions={handleLoadFilteredTransactions}
        onSaveSettings={handleSaveSettings}
        onGenerateReport={handleGenerateReport}
        onDownloadReport={handleDownloadReport}
        onCreateSchedule={handleCreateSchedule}
        onSimulateData={handleSimulateData}
        onResetData={handleResetData}
        onVerifyAudit={handleVerifyAudit}
      />
      {loadingData || dataError || toast ? (
        <div className="fixed bottom-4 right-4 bg-white border border-gray-200 px-3 py-2 rounded text-xs font-mono text-gray-600 shadow-sm">
          {loadingData ? "Atualizando dados..." : dataError ? `Erro de dados: ${dataError}` : toast}
        </div>
      ) : null}
    </>
  );
}
