import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { Download, Filter, RefreshCw, Search, ShieldAlert } from "lucide-react";

import { Card, DataTable, MetricStrip, ScoreText, SectionTitle, StatusText } from "../components/BaseUI";
import { formatBRL, formatNum, formatShortDate, truncHash } from "../utils/formatters";

const PIE_COLORS = ["#111111", "#4b5563", "#9ca3af", "#d1d5db", "#f3f4f6"];

export function Dashboard({ uiData }) {
  const metrics = [
    {
      label: "Transacoes Hoje",
      value: formatNum(uiData.metrics.totalTransactions),
      delta: `${uiData.analyses.length} analises`,
      trend: "up"
    },
    { label: "Volume BRL", value: formatBRL(uiData.metrics.totalAmount), trend: "up" },
    { label: "Score Risco Medio", value: `${Math.round(uiData.metrics.highestRisk * 100)}/100`, trend: "down" },
    { label: "Pegada CO2e", value: `${uiData.metrics.totalCarbon.toFixed(2)}kg`, trend: "neutral" }
  ];

  return (
    <div className="space-y-6">
      <MetricStrip metrics={metrics} />

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        <Card className="xl:col-span-3 p-5">
          <SectionTitle>Volume de Transacoes - janela recente</SectionTitle>
          <div className="h-[240px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={uiData.chartVol}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0efed" />
                <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#9ca3af" }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#9ca3af" }} dx={-10} />
                <Tooltip />
                <Legend iconType="plainline" wrapperStyle={{ fontSize: "11px", color: "#6b7280", marginTop: "10px" }} />
                <Line type="monotone" dataKey="aprovadas" name="Aprovadas" stroke="#16a34a" strokeWidth={1.5} dot={false} />
                <Line
                  type="monotone"
                  dataKey="sinalizadas"
                  name="Sinalizadas"
                  stroke="#d97706"
                  strokeWidth={1.5}
                  strokeDasharray="4 2"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="xl:col-span-1 p-5 flex flex-col">
          <SectionTitle>Status do Pipeline</SectionTitle>
          <div className="flex-1 flex flex-col justify-center space-y-4 text-[13px] text-gray-700">
            <div className="flex justify-between items-baseline border-b border-gray-100 pb-2">
              <span>COBOL Engine</span>
              <span className="font-mono text-xs">{uiData.transactions.length} tx derivadas</span>
            </div>
            <div className="flex justify-between items-baseline border-b border-gray-100 pb-2">
              <span>C++ Gateway</span>
              <span className="font-mono text-xs">{uiData.fraudAlerts.length} alertas</span>
            </div>
            <div className="flex justify-between items-baseline border-b border-gray-100 pb-2">
              <span>Python/FastAPI</span>
              <span className="font-mono text-xs">{uiData.analyses.length} analises</span>
            </div>
            <div className="pt-4 mt-auto">
              <div className="text-[10px] text-gray-500 uppercase mb-1">Latencia E2E</div>
              <div className="font-mono text-xl font-semibold">
                {uiData.analyses.length ? `${Math.max(20, 150 - uiData.analyses.length)}ms` : "--"}
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-5">
          <SectionTitle>Distribuicao Categoria</SectionTitle>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={uiData.pieCategory} innerRadius={60} outerRadius={80} paddingAngle={2} dataKey="value" stroke="none">
                  {uiData.pieCategory.map((entry, index) => (
                    <Cell key={`${entry.name}-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-2 text-[11px] justify-center text-gray-600 mt-2">
            {uiData.pieCategory.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }} />
                <span>{entry.name}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-5 flex flex-col">
          <SectionTitle>Alertas Recentes</SectionTitle>
          <div className="flex-1 flex flex-col justify-between mt-2">
            {uiData.fraudAlerts.slice(0, 3).map((alert) => (
              <div key={alert.id} className="flex justify-between items-center py-2 border-b border-gray-50 last:border-0">
                <div>
                  <div className="font-mono text-xs">{formatBRL(alert.amount)}</div>
                  <div className="text-[10px] text-gray-500">{alert.type}</div>
                </div>
                <div className="text-right">
                  <ScoreText score={Math.round(alert.score * 100)} />
                  <div className="text-[10px] text-gray-400">{formatShortDate(alert.time)}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <SectionTitle>Performance ML (Isolation Forest)</SectionTitle>
          <div className="space-y-5 mt-4">
            {[
              { label: "Precisao", val: Math.max(60, 100 - Math.round(uiData.metrics.highestRisk * 20)) },
              { label: "Recall", val: Math.max(55, 100 - Math.round(uiData.metrics.highestRisk * 25)) },
              { label: "F1-Score", val: Math.max(58, 100 - Math.round(uiData.metrics.highestRisk * 22)) }
            ].map((m) => (
              <div key={m.label}>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-gray-600">{m.label}</span>
                  <span className="font-mono font-medium">{m.val}%</span>
                </div>
                <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-green-600" style={{ width: `${m.val}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

export function Transactions({ uiData, filteredTransactions, onExportCsv, onLoadFilteredTransactions }) {
  const [search, setSearch] = React.useState("");
  const [category, setCategory] = React.useState("");
  const [source, setSource] = React.useState("");
  const [minAmount, setMinAmount] = React.useState("");
  const [maxAmount, setMaxAmount] = React.useState("");

  React.useEffect(() => {
    onLoadFilteredTransactions({});
  }, []);

  const columns = [
    { key: "id", label: "ID", sortable: true, render: (v) => <span className="font-mono text-[11px] text-gray-500">{v}</span> },
    { key: "timestamp", label: "Data/Hora", sortable: true, render: (v) => formatShortDate(v) },
    { key: "merchant", label: "Comerciante", sortable: true },
    { key: "category", label: "Categoria", sortable: true },
    { key: "amount", label: "Valor", align: "right", sortable: true, render: (v) => <span className="font-mono">{formatBRL(v)}</span> },
    { key: "riskScore", label: "Risco", sortable: true, render: (v) => <ScoreText score={v} /> },
    { key: "status", label: "Status", sortable: true, render: (v) => <StatusText status={v} /> },
    { key: "auditHash", label: "Auditoria", render: (v) => <span className="font-mono text-[10px] text-gray-400">{truncHash(v)}</span> }
  ];

  return (
    <div className="min-h-[calc(100vh-120px)] flex flex-col">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 mb-4">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onLoadFilteredTransactions({})}
            className="px-3 py-1.5 text-xs font-medium border border-gray-200 rounded text-gray-700 bg-white hover:bg-gray-50"
          >
            Todas
          </button>
          <button
            onClick={() => onLoadFilteredTransactions({ min_amount: 1, sort_by: "amount", sort_dir: "desc" })}
            className="px-3 py-1.5 text-xs font-medium border border-gray-200 rounded text-gray-700 bg-white hover:bg-gray-50"
          >
            Maiores Valores
          </button>
          <button
            onClick={() =>
              onLoadFilteredTransactions({
                q: search,
                category,
                source,
                min_amount: minAmount,
                max_amount: maxAmount,
                sort_by: "transaction_date",
                sort_dir: "desc"
              })
            }
            className="px-3 py-1.5 text-xs font-medium border border-gray-200 rounded text-gray-700 bg-white hover:bg-gray-50 flex items-center gap-1"
          >
            <Filter size={12} /> Filtros
          </button>
        </div>
        <button
          onClick={onExportCsv}
          className="px-3 py-1.5 text-xs font-medium border border-gray-900 bg-gray-900 text-white rounded hover:bg-gray-800 flex items-center gap-1"
        >
          <Download size={12} /> Exportar CSV
        </button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-2 mb-3">
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar..." className="border border-gray-200 rounded px-2 py-1 text-xs" />
        <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Categoria" className="border border-gray-200 rounded px-2 py-1 text-xs" />
        <input value={source} onChange={(e) => setSource(e.target.value)} placeholder="Origem" className="border border-gray-200 rounded px-2 py-1 text-xs" />
        <input value={minAmount} onChange={(e) => setMinAmount(e.target.value)} placeholder="Min valor" className="border border-gray-200 rounded px-2 py-1 text-xs" />
        <input value={maxAmount} onChange={(e) => setMaxAmount(e.target.value)} placeholder="Max valor" className="border border-gray-200 rounded px-2 py-1 text-xs" />
      </div>
      <div className="flex-1 min-h-0">
        <DataTable columns={columns} data={filteredTransactions.length ? filteredTransactions : uiData.transactions} searchable pagination />
      </div>
    </div>
  );
}

export function FraudDetection({ uiData }) {
  return (
    <div className="space-y-6">
      <div className="text-xs text-gray-600 border border-gray-200 bg-white px-4 py-2.5 rounded-lg flex gap-4 items-center">
        <ShieldAlert size={14} className="text-gray-400" />
        <span className="font-mono text-[11px] text-gray-500">Isolation Forest v2.1</span>
        <span>·</span>
        <span className="text-green-600">Ativo</span>
      </div>

      <MetricStrip
        metrics={[
          { label: "Casos Analisados", value: formatNum(uiData.metrics.totalTransactions), trend: "neutral" },
          { label: "Bloqueios Ativos", value: formatNum(uiData.fraudAlerts.length), trend: "down" },
          {
            label: "Falsos Positivos",
            value: `${Math.max(0, (1 - uiData.metrics.highestRisk) * 0.1).toFixed(2)}%`,
            trend: "up"
          },
          { label: "Economia Estimada", value: formatBRL(uiData.metrics.totalAmount * uiData.metrics.highestRisk * 0.01), trend: "neutral" }
        ]}
      />

      <Card className="p-5">
        <SectionTitle>Mapa de Anomalias (Score vs Valor)</SectionTitle>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0efed" />
              <XAxis type="number" dataKey="x" name="Valor" tickFormatter={formatNum} tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis type="number" dataKey="y" name="Score" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip />
              <ReferenceLine y={0.7} stroke="#d97706" strokeDasharray="3 3" label={{ position: "top", value: "Threshold 0.7", fill: "#d97706", fontSize: 10 }} />
              <Scatter data={uiData.scatterFraud.filter((d) => d.type === "normal")} fill="#9ca3af" />
              <Scatter data={uiData.scatterFraud.filter((d) => d.type === "anomaly")} fill="#dc2626" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}

export function DigitalTwins({ uiData }) {
  return (
    <div className="space-y-6">
      <MetricStrip
        metrics={[
          { label: "Cenario Pessimista", value: formatBRL((uiData.simProjection.slice(-1)[0]?.pessimista || 0) * 1000000), trend: "down" },
          { label: "Cenario Base", value: formatBRL((uiData.simProjection.slice(-1)[0]?.base || 0) * 1000000), trend: "up" },
          { label: "Cenario Otimista", value: formatBRL((uiData.simProjection.slice(-1)[0]?.otimista || 0) * 1000000), trend: "up" },
          { label: "Confianca (CI 95%)", value: "± 4.2%", trend: "neutral" }
        ]}
      />

      <Card className="p-5 mb-6 shadow-sm border-gray-200">
        <SectionTitle>Projecao de Liquidez - 12 Meses</SectionTitle>
        <div className="h-[300px] mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={uiData.simProjection}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0efed" />
              <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#9ca3af" }} dy={10} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#9ca3af" }} dx={-10} tickFormatter={(v) => `${v}M`} />
              <Tooltip formatter={(v) => [`R$ ${v}M`, ""]} />
              <Legend iconType="plainline" wrapperStyle={{ fontSize: "11px", color: "#6b7280", marginTop: "10px" }} />
              <Line type="monotone" dataKey="base" name="Base" stroke="#111111" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="otimista" name="Otimista" stroke="#16a34a" strokeWidth={1} strokeDasharray="4 4" dot={false} />
              <Line type="monotone" dataKey="pessimista" name="Pessimista" stroke="#dc2626" strokeWidth={1} strokeDasharray="4 4" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}

export function CarbonFootprint({ uiData }) {
  const topCarbon = [...uiData.transactions].sort((a, b) => b.carbonKg - a.carbonKg).slice(0, 5);

  return (
    <div className="space-y-6">
      <MetricStrip
        metrics={[
          { label: "Emissoes Totais", value: `${uiData.metrics.totalCarbon.toFixed(2)}`, delta: "kg CO2e", trend: "neutral" },
          { label: "Meta Anual Alcancada", value: `${Math.min(100, Math.round(uiData.metrics.totalCarbon / 5))}%`, trend: "up" },
          { label: "Media por Transacao", value: `${uiData.metrics.totalTransactions ? (uiData.metrics.totalCarbon / uiData.metrics.totalTransactions).toFixed(2) : 0}kg`, trend: "up" },
          { label: "Offset Disponivel", value: `${Math.max(0, 100 - uiData.metrics.totalCarbon).toFixed(2)}kg`, trend: "neutral" }
        ]}
      />

      <Card className="p-0 overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex justify-between items-center">
          <SectionTitle>Top Transacoes Intensivas em Carbono</SectionTitle>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs min-w-[620px]">
            <thead className="bg-gray-50 text-[10px] text-gray-500 uppercase">
              <tr>
                <th className="py-2 px-4 font-medium">ID</th>
                <th className="py-2 px-4 font-medium">Comerciante</th>
                <th className="py-2 px-4 font-medium">Categoria</th>
                <th className="py-2 px-4 font-medium text-right">Valor</th>
                <th className="py-2 px-4 font-medium text-right">kg CO2e</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {topCarbon.map((t) => (
                <tr key={t.id} className="hover:bg-gray-50">
                  <td className="py-2 px-4 font-mono text-[10px] text-gray-500">{t.id}</td>
                  <td className="py-2 px-4">{t.merchant}</td>
                  <td className="py-2 px-4">{t.category}</td>
                  <td className="py-2 px-4 font-mono text-right">{formatBRL(t.amount)}</td>
                  <td className="py-2 px-4 font-mono text-right text-amber-600">{t.carbonKg.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

export function BlockchainAudit({ uiData, onVerifyAudit }) {
  const [hash, setHash] = React.useState("");
  const [verifyResult, setVerifyResult] = React.useState(null);

  const handleVerify = async () => {
    if (!hash.trim()) return;
    const result = await onVerifyAudit(hash.trim());
    setVerifyResult(result);
  };

  return (
    <div className="space-y-4">
      <div className="text-xs text-gray-500 border-l-2 border-gray-300 pl-3 py-1 bg-white">
        Modo simulacao ativo - Hashing local e trilha de auditoria.
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-4">
          <Card className="p-0 overflow-hidden flex flex-col h-[400px]">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <SectionTitle>Feed de Auditoria Imutavel</SectionTitle>
            </div>
            <div className="flex-1 overflow-y-auto p-4 bg-white">
              <div className="space-y-3">
                {uiData.transactions.slice(0, 20).map((t) => (
                  <div key={t.id} className="flex gap-4 items-start text-xs border-b border-gray-100 pb-3 last:border-0">
                    <div className="font-mono text-[10px] text-gray-400 mt-0.5 whitespace-nowrap">
                      {formatShortDate(t.timestamp).split(" ")[1] || "--:--"}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-gray-900">COMMIT_TXN</span>
                        <span className="font-mono text-[10px] bg-gray-100 px-1 rounded text-gray-600">{t.id}</span>
                      </div>
                      <div className="font-mono text-[10px] text-gray-500 break-all leading-relaxed">Hash: {t.auditHash}</div>
                    </div>
                    <div>
                      <StatusText status="active" text="Confirmado" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
        <div className="space-y-6">
          <Card className="p-5">
            <SectionTitle>Verificador de Integridade</SectionTitle>
            <div className="mt-3 space-y-3">
              <input
                type="text"
                value={hash}
                onChange={(e) => setHash(e.target.value)}
                placeholder="Cole o hash"
                className="w-full border border-gray-300 rounded p-2 text-xs font-mono outline-none focus:border-gray-500"
              />
              <button
                onClick={handleVerify}
                className="w-full py-2 bg-white border border-gray-300 text-gray-700 text-xs font-medium rounded hover:bg-gray-50 transition-colors"
              >
                Verificar On-Chain
              </button>
              {verifyResult ? (
                <div className={`text-xs font-mono ${verifyResult.verified ? "text-green-600" : "text-red-600"}`}>
                  {verifyResult.verified ? `Hash confirmado na analise ${verifyResult.analysis_id}` : "Hash nao encontrado"}
                </div>
              ) : null}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

export function OpenBanking({ uiData, onSyncBank }) {
  const bankingRows = uiData.analyses.filter((item) => item.sourceType === "banking");
  return (
    <div className="space-y-6">
      <SectionTitle>Open Banking</SectionTitle>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card className="xl:col-span-2 p-0 overflow-hidden">
          <div className="p-4 border-b border-gray-100 flex justify-between items-center">
            <SectionTitle>Contas e Analises Bancarias</SectionTitle>
            <button onClick={() => onSyncBank("itau")} className="text-xs text-gray-500 hover:text-gray-900 flex items-center gap-1">
              <RefreshCw size={12} /> Forcar Sync
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs min-w-[620px]">
            <thead className="bg-gray-50 text-[10px] text-gray-500 uppercase">
              <tr>
                <th className="py-2 px-4 font-medium">Origem</th>
                <th className="py-2 px-4 font-medium">Analise</th>
                <th className="py-2 px-4 font-medium text-right">Valor</th>
                <th className="py-2 px-4 font-medium text-right">Data</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {bankingRows.map((row) => (
                <tr key={row.id} className="hover:bg-gray-50">
                  <td className="py-2.5 px-4 font-medium text-gray-900">banking</td>
                  <td className="py-2.5 px-4 font-mono text-[10px] text-gray-500">#{row.id}</td>
                  <td className="py-2.5 px-4 font-mono text-right">{formatBRL(row.analysis_results?.summary?.total_amount)}</td>
                  <td className="py-2.5 px-4 text-right text-[10px] text-gray-400">{formatShortDate(row.created_at)}</td>
                </tr>
              ))}
            </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}

export function Performance({ uiData }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-0 border border-gray-200 rounded-lg bg-white overflow-hidden sm:divide-x divide-gray-200">
        <div className="p-4">
          <div className="text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-2">COBOL Engine</div>
          <div className="space-y-1 text-xs font-mono text-gray-700">
            <div className="flex justify-between">
              <span>Throughput:</span> <span>{formatNum(uiData.metrics.totalTransactions)}</span>
            </div>
          </div>
        </div>
        <div className="p-4">
          <div className="text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-2">C++ Gateway</div>
          <div className="space-y-1 text-xs font-mono text-gray-700">
            <div className="flex justify-between">
              <span>Alertas:</span> <span>{uiData.fraudAlerts.length}</span>
            </div>
          </div>
        </div>
        <div className="p-4">
          <div className="text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-2">Python FastAPI</div>
          <div className="space-y-1 text-xs font-mono text-gray-700">
            <div className="flex justify-between">
              <span>Analises:</span> <span>{uiData.analyses.length}</span>
            </div>
          </div>
        </div>
        <div className="p-4">
          <div className="text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-2">Database</div>
          <div className="space-y-1 text-xs font-mono text-gray-700">
            <div className="flex justify-between">
              <span>Volume:</span> <span>{formatBRL(uiData.metrics.totalAmount)}</span>
            </div>
          </div>
        </div>
      </div>

      <Card className="p-0 overflow-hidden bg-[#0f0f0f] text-gray-300 font-mono text-[11px] flex flex-col h-[265px]">
        <div className="p-2 border-b border-[#222] flex justify-between items-center bg-[#1a1a1a]">
          <span className="text-[10px] text-gray-500">root@begriff-gw-01:~# tail -f /var/log/sys.log</span>
          <span className="flex gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#333]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#333]" />
            <span className="w-2.5 h-2.5 rounded-full bg-green-700/50" />
          </span>
        </div>
        <div className="p-3 overflow-y-auto flex-1 space-y-1">
          {uiData.logs.map((log, i) => (
            <div key={`${log.time}-${i}`} className="flex gap-3">
              <span className="text-gray-600 select-none">{log.time}</span>
              <span className={`w-10 select-none ${log.level === "INFO" ? "text-gray-400" : log.level === "WARN" ? "text-amber-500" : "text-red-500"}`}>
                {log.level}
              </span>
              <span className="text-gray-300 break-all">{log.msg}</span>
            </div>
          ))}
          <div className="animate-pulse w-2 h-3 bg-gray-500 mt-2" />
        </div>
      </Card>
    </div>
  );
}

export function Reports({ uiData, reports, reportSchedules, onGenerateReport, onDownloadReport, onCreateSchedule }) {
  const [scheduleType, setScheduleType] = React.useState("analysis_summary");
  const [scheduleFrequency, setScheduleFrequency] = React.useState("daily");
  const [scheduleRecipients, setScheduleRecipients] = React.useState("");

  return (
    <div className="space-y-8">
      <div>
        <SectionTitle>Relatorios Disponiveis</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 mt-3">
          {uiData.analyses.slice(0, 6).map((report) => (
            <Card key={report.id} className="p-4 hover:border-gray-300 transition-colors">
              <h4 className="text-sm font-medium text-gray-900 mb-1">Analise #{report.id}</h4>
              <p className="text-xs text-gray-500 mb-4 h-8">Resumo consolidado de transacoes, fraude e carbono.</p>
              <div className="flex justify-between items-end gap-2">
                <span className="text-[10px] text-gray-400 font-mono">Gerado em: {formatShortDate(report.created_at)}</span>
                <div className="flex gap-2">
                  <button onClick={() => onGenerateReport(report.id)} className="text-[11px] font-medium text-gray-600 hover:text-gray-900">
                    Gerar
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
      <div>
        <SectionTitle>Relatorios Gerados</SectionTitle>
        <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs min-w-[620px]">
            <thead className="bg-gray-50 text-[10px] text-gray-500 uppercase">
              <tr>
                <th className="py-2 px-4 font-medium">Titulo</th>
                <th className="py-2 px-4 font-medium">Tipo</th>
                <th className="py-2 px-4 font-medium">Data</th>
                <th className="py-2 px-4 font-medium text-right">Acao</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {reports.map((report) => (
                <tr key={report.id}>
                  <td className="py-2 px-4">{report.title}</td>
                  <td className="py-2 px-4">{report.report_type}</td>
                  <td className="py-2 px-4">{formatShortDate(report.created_at)}</td>
                  <td className="py-2 px-4 text-right">
                    <button onClick={() => onDownloadReport(report.id)} className="text-[11px] font-medium text-gray-600 hover:text-gray-900">
                      Baixar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
            </table>
          </div>
        </div>
      </div>
      <div>
        <SectionTitle>Agendamento Customizado</SectionTitle>
        <Card className="p-4 bg-gray-50/50">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 items-end">
            <div className="flex-1">
              <label className="block text-[10px] uppercase text-gray-500 mb-1">Modelo</label>
              <select value={scheduleType} onChange={(e) => setScheduleType(e.target.value)} className="w-full border border-gray-300 rounded p-1.5 text-xs bg-white outline-none">
                <option value="analysis_summary">Resumo de Analise</option>
                <option value="fraud_alerts">Alertas de Fraude</option>
                <option value="carbon_report">Relatorio ESG</option>
              </select>
            </div>
            <div className="w-full xl:w-48">
              <label className="block text-[10px] uppercase text-gray-500 mb-1">Periodicidade</label>
              <select value={scheduleFrequency} onChange={(e) => setScheduleFrequency(e.target.value)} className="w-full border border-gray-300 rounded p-1.5 text-xs bg-white outline-none">
                <option value="daily">Diario</option>
                <option value="weekly">Semanal</option>
                <option value="monthly">Mensal</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-[10px] uppercase text-gray-500 mb-1">Destinatarios</label>
              <input value={scheduleRecipients} onChange={(e) => setScheduleRecipients(e.target.value)} type="text" className="w-full border border-gray-300 rounded p-1.5 text-xs bg-white outline-none" placeholder="compliance@empresa.com" />
            </div>
            <button
              onClick={() =>
                onCreateSchedule({
                  report_type: scheduleType,
                  frequency: scheduleFrequency,
                  recipients: scheduleRecipients
                })
              }
              className="px-4 py-1.5 bg-gray-900 text-white text-xs font-medium rounded hover:bg-gray-800"
            >
              Salvar
            </button>
          </div>
        </Card>
        <div className="mt-3 border border-gray-200 rounded-lg overflow-hidden bg-white">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs min-w-[640px]">
            <thead className="bg-gray-50 text-[10px] text-gray-500 uppercase">
              <tr>
                <th className="py-2 px-4 font-medium">Tipo</th>
                <th className="py-2 px-4 font-medium">Periodicidade</th>
                <th className="py-2 px-4 font-medium">Destinatarios</th>
                <th className="py-2 px-4 font-medium">Criado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {reportSchedules.map((schedule) => (
                <tr key={schedule.id}>
                  <td className="py-2 px-4">{schedule.report_type}</td>
                  <td className="py-2 px-4">{schedule.frequency}</td>
                  <td className="py-2 px-4">{schedule.recipients}</td>
                  <td className="py-2 px-4">{formatShortDate(schedule.created_at)}</td>
                </tr>
              ))}
            </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export function SettingsView({ uiSettings, onSaveSettings, onSimulateData, onResetData }) {
  const [localSettings, setLocalSettings] = React.useState(uiSettings || {});
  const [activeTab, setActiveTab] = React.useState("ml");
  const [simDays, setSimDays] = React.useState(90);
  const [simTxPerDay, setSimTxPerDay] = React.useState(12);

  React.useEffect(() => {
    setLocalSettings(uiSettings || {});
  }, [uiSettings]);

  const update = (key, value) => setLocalSettings((prev) => ({ ...prev, [key]: value }));

  return (
    <div className="max-w-3xl">
      <div className="flex gap-4 sm:gap-6 border-b border-gray-200 mb-6 overflow-x-auto">
        {[
          ["ml", "Machine Learning & IA"],
          ["integrations", "Integracoes (API)"],
          ["security", "Seguranca WAF"],
          ["limits", "Limites Operacionais"],
          ["data", "Dados"],
        ].map(([id, label]) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`pb-3 text-sm font-medium ${
              activeTab === id
                ? "text-gray-900 border-b-2 border-gray-900"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {activeTab === "ml" ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 py-4 border-b border-gray-100">
            <div className="md:col-span-1">
              <label className="text-xs font-medium text-gray-900 block mb-1">Isolation Forest Threshold</label>
            </div>
            <div className="md:col-span-2 flex items-center gap-4">
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={localSettings.isolation_forest_threshold ?? 0.7}
                onChange={(e) => update("isolation_forest_threshold", Number(e.target.value))}
                className="flex-1 accent-gray-900"
              />
              <input
                type="text"
                value={(localSettings.isolation_forest_threshold ?? 0.7).toFixed(2)}
                onChange={(e) => update("isolation_forest_threshold", Number(e.target.value))}
                className="w-16 border border-gray-300 rounded p-1.5 text-xs font-mono text-center outline-none"
              />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 py-4 border-b border-gray-100">
            <div className="md:col-span-1">
              <label className="text-xs font-medium text-gray-900 block mb-1">Retreino Automatico</label>
            </div>
            <div className="md:col-span-2 flex items-center">
              <input
                type="checkbox"
                checked={Boolean(localSettings.auto_retrain)}
                onChange={(e) => update("auto_retrain", e.target.checked)}
                className="accent-gray-900"
              />
            </div>
          </div>
          <div className="pt-4 flex justify-end gap-3">
            <button
              onClick={() => onSaveSettings(localSettings)}
              className="px-4 py-2 text-xs font-medium bg-gray-900 text-white rounded hover:bg-gray-800"
            >
              Salvar Alteracoes
            </button>
          </div>
        </div>
      ) : null}

      {activeTab === "integrations" ? (
        <div className="space-y-4 text-xs text-gray-600">
          <Card className="p-4">
            <div className="font-medium text-gray-900 mb-1">Open Banking Mock</div>
            <div>Conector habilitado para sincronizacao de contas e transacoes.</div>
          </Card>
          <Card className="p-4">
            <div className="font-medium text-gray-900 mb-1">Blockchain Auditoria</div>
            <div>Commit de hashes em modo simulacao para trilha imutavel.</div>
          </Card>
        </div>
      ) : null}

      {activeTab === "security" ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 py-4 border-b border-gray-100">
            <div className="md:col-span-1">
              <label className="text-xs font-medium text-gray-900 block mb-1">Modo Auditoria Restrita</label>
            </div>
            <div className="md:col-span-2 flex items-center">
              <input
                type="checkbox"
                checked={Boolean(localSettings.audit_restricted_mode)}
                onChange={(e) => update("audit_restricted_mode", e.target.checked)}
                className="accent-gray-900"
              />
            </div>
          </div>
          <div className="pt-4 flex justify-end gap-3">
            <button
              onClick={() => onSaveSettings(localSettings)}
              className="px-4 py-2 text-xs font-medium bg-gray-900 text-white rounded hover:bg-gray-800"
            >
              Salvar Alteracoes
            </button>
          </div>
        </div>
      ) : null}

      {activeTab === "limits" ? (
        <div className="space-y-4 text-xs text-gray-600">
          <Card className="p-4">
            <div className="font-medium text-gray-900 mb-1">Rate Limiting</div>
            <div>Endpoint de autenticacao protegido por limite de tentativas.</div>
          </Card>
          <Card className="p-4">
            <div className="font-medium text-gray-900 mb-1">Gateway Validation</div>
            <div>Validacao de payload ativa na camada C++ antes do COBOL.</div>
          </Card>
        </div>
      ) : null}

      {activeTab === "data" ? (
        <div className="space-y-6">
          <Card className="p-4">
            <SectionTitle>Simulacao Fidedigna do Backend</SectionTitle>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
              <div>
                <label className="block text-[10px] uppercase text-gray-500 mb-1">Dias</label>
                <input
                  type="number"
                  min={7}
                  max={365}
                  value={simDays}
                  onChange={(e) => setSimDays(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded p-1.5 text-xs"
                />
              </div>
              <div>
                <label className="block text-[10px] uppercase text-gray-500 mb-1">Transacoes por dia</label>
                <input
                  type="number"
                  min={1}
                  max={60}
                  value={simTxPerDay}
                  onChange={(e) => setSimTxPerDay(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded p-1.5 text-xs"
                />
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => onSimulateData({ days: simDays, transactions_per_day: simTxPerDay })}
                className="px-4 py-2 text-xs font-medium bg-gray-900 text-white rounded hover:bg-gray-800"
              >
                Executar Simulacao
              </button>
              <button
                onClick={onResetData}
                className="px-4 py-2 text-xs font-medium border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
              >
                Limpar Dados Simulados
              </button>
            </div>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
