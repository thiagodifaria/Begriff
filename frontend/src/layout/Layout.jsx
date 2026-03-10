import { useState } from "react";
import {
  Activity,
  Copy,
  Database,
  FileText,
  Globe,
  LayoutDashboard,
  Link2,
  List,
  LogOut,
  Menu,
  Search,
  Settings,
  ShieldAlert,
  SidebarClose,
  SidebarOpen,
  X
} from "lucide-react";

import {
  BlockchainAudit,
  CarbonFootprint,
  Dashboard,
  DigitalTwins,
  FraudDetection,
  OpenBanking,
  Performance,
  Reports,
  SettingsView,
  Transactions
} from "../views/pages";

export default function Layout({
  currentPage,
  setCurrentPage,
  onLogout,
  uiData,
  filteredTransactions,
  reports,
  reportSchedules,
  uiSettings,
  user,
  onSyncBank,
  onExportCsv,
  onLoadFilteredTransactions,
  onSaveSettings,
  onGenerateReport,
  onDownloadReport,
  onCreateSchedule,
  onSimulateData,
  onResetData,
  onVerifyAudit
}) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "transactions", label: "Transacoes", icon: List },
    { id: "fraud", label: "Deteccao de Fraude", icon: ShieldAlert },
    { id: "twins", label: "Gemeos Digitais", icon: Copy },
    { id: "carbon", label: "Pegada de Carbono", icon: Globe },
    { id: "blockchain", label: "Auditoria Blockchain", icon: Database },
    { id: "openbanking", label: "Open Banking", icon: Link2 }
  ];

  const systemItems = [
    { id: "performance", label: "Performance E2E", icon: Activity },
    { id: "reports", label: "Relatorios", icon: FileText },
    { id: "settings", label: "Configuracoes", icon: Settings }
  ];

  const pageTitles = {
    dashboard: "Inteligencia Executiva",
    transactions: "Transacoes e Liquidacoes",
    fraud: "Prevencao a Fraude (ML)",
    twins: "Simulacoes e Cenarios",
    carbon: "Controle ESG e Carbono",
    blockchain: "Ledger Imutavel",
    openbanking: "Agregacao Financeira",
    performance: "Monitoramento de Infraestrutura",
    reports: "Central de Relatorios",
    settings: "Configuracoes do Sistema"
  };

  const isCompact = collapsed && !mobileOpen;
  const sidebarWidth = isCompact ? "w-[280px] md:w-[92px]" : "w-[280px]";

  const MenuButton = ({ item }) => (
    <button
      key={item.id}
      onClick={() => {
        setCurrentPage(item.id);
        setMobileOpen(false);
      }}
      title={isCompact ? item.label : undefined}
      className={`w-full flex items-center ${isCompact ? "justify-center" : "justify-start"} gap-2.5 px-2.5 py-2 rounded text-[13px] transition-colors ${
        currentPage === item.id
          ? "font-medium text-gray-900 bg-gray-200/60"
          : "text-gray-600 hover:bg-gray-200/50 hover:text-gray-900"
      }`}
    >
      <item.icon size={15} className={currentPage === item.id ? "text-gray-900" : "text-gray-400"} />
      {!isCompact ? <span className="truncate">{item.label}</span> : null}
    </button>
  );

  return (
    <div className="flex h-screen bg-[#fafaf9] text-gray-900 font-sans overflow-hidden selection:bg-gray-200">
      <div
        className={`fixed inset-0 bg-black/35 z-30 transition-opacity md:hidden ${
          mobileOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
        onClick={() => setMobileOpen(false)}
      />

      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 ${sidebarWidth} bg-[#f5f4f2] border-r border-gray-200 flex flex-col shrink-0 transform transition-all duration-300 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        <div className="h-12 border-b border-gray-200 flex items-center px-4 justify-between">
          <span className="font-semibold text-[15px] tracking-tight text-gray-900">{isCompact ? "Bg" : "Begriff"}</span>
          <button
            className="hidden md:inline-flex text-gray-500 hover:text-gray-900"
            onClick={() => setCollapsed((v) => !v)}
            title={collapsed ? "Expandir sidebar" : "Recolher sidebar"}
          >
            {collapsed ? <SidebarOpen size={15} /> : <SidebarClose size={15} />}
          </button>
          <button className="md:hidden text-gray-500 hover:text-gray-900" onClick={() => setMobileOpen(false)}>
            <X size={16} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          {!isCompact ? (
            <div className="px-4 mb-2">
              <span className="text-[10px] font-medium text-gray-400 uppercase tracking-widest">Plataforma</span>
            </div>
          ) : null}
          <nav className="space-y-0.5 px-2">{menuItems.map((item) => <MenuButton key={item.id} item={item} />)}</nav>

          {!isCompact ? (
            <div className="px-4 mt-6 mb-2">
              <span className="text-[10px] font-medium text-gray-400 uppercase tracking-widest">Sistema</span>
            </div>
          ) : null}
          <nav className="space-y-0.5 px-2">{systemItems.map((item) => <MenuButton key={item.id} item={item} />)}</nav>
        </div>

        <div className="p-4 border-t border-gray-200">
          <div className={`flex items-center ${isCompact ? "justify-center" : "justify-between"} mb-3`}>
            {!isCompact ? (
              <div>
                <div className="text-xs font-medium text-gray-900 truncate max-w-[180px]">{user?.email || "Admin User"}</div>
                <div className="text-[10px] text-gray-500">Sysadmin</div>
              </div>
            ) : null}
            <button onClick={onLogout} className="text-gray-400 hover:text-gray-900" title="Sair">
              <LogOut size={14} />
            </button>
          </div>
          {!isCompact ? <div className="text-[10px] text-gray-400 font-mono">v1.6.0-stable</div> : null}
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <div className="h-12 border-b border-gray-200 bg-[#fafaf9] flex items-center justify-between px-3 sm:px-6 shrink-0 gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <button className="md:hidden text-gray-500 hover:text-gray-900" onClick={() => setMobileOpen(true)}>
              <Menu size={16} />
            </button>
            <h1 className="text-[15px] font-semibold text-gray-900 truncate">{pageTitles[currentPage]}</h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative hidden sm:block">
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar (Cmd+K)"
                className="pl-8 pr-3 py-1.5 text-xs bg-white border border-gray-200 rounded w-48 lg:w-64 outline-none focus:border-gray-400 placeholder:text-gray-400"
              />
            </div>
            <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-[10px] font-medium text-gray-600 border border-gray-300">
              AD
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 sm:p-6">
          <div className="max-w-6xl mx-auto">
            {currentPage === "dashboard" && <Dashboard uiData={uiData} />}
            {currentPage === "transactions" && (
              <Transactions
                uiData={uiData}
                filteredTransactions={filteredTransactions}
                onExportCsv={onExportCsv}
                onLoadFilteredTransactions={onLoadFilteredTransactions}
              />
            )}
            {currentPage === "fraud" && <FraudDetection uiData={uiData} />}
            {currentPage === "twins" && <DigitalTwins uiData={uiData} />}
            {currentPage === "carbon" && <CarbonFootprint uiData={uiData} />}
            {currentPage === "blockchain" && <BlockchainAudit uiData={uiData} onVerifyAudit={onVerifyAudit} />}
            {currentPage === "openbanking" && <OpenBanking uiData={uiData} onSyncBank={onSyncBank} />}
            {currentPage === "performance" && <Performance uiData={uiData} />}
            {currentPage === "reports" && (
              <Reports
                uiData={uiData}
                reports={reports}
                reportSchedules={reportSchedules}
                onGenerateReport={onGenerateReport}
                onDownloadReport={onDownloadReport}
                onCreateSchedule={onCreateSchedule}
              />
            )}
            {currentPage === "settings" && (
              <SettingsView
                uiSettings={uiSettings}
                onSaveSettings={onSaveSettings}
                onSimulateData={onSimulateData}
                onResetData={onResetData}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
