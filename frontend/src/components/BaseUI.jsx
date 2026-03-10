import { useState } from "react";
import { ArrowUpDown, Search } from "lucide-react";

export const Card = ({ children, className = "" }) => (
  <div className={`bg-white border border-gray-200 rounded-lg ${className}`}>{children}</div>
);

export const SectionTitle = ({ children }) => (
  <h3 className="text-[10px] font-medium text-gray-500 uppercase tracking-widest mb-3">{children}</h3>
);

export const MetricStrip = ({ metrics }) => (
  <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 sm:divide-x divide-gray-200 border border-gray-200 rounded-lg bg-white overflow-hidden mb-6">
    {metrics.map((m, i) => (
      <div key={`${m.label}-${i}`} className="px-4 sm:px-5 py-4 border-b sm:border-b-0 border-gray-100 last:border-b-0">
        <div className="text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-1">{m.label}</div>
        <div className="flex items-baseline gap-2">
          <div className="text-2xl font-mono font-semibold text-gray-900">{m.value}</div>
          {m.delta ? (
            <div
              className={`text-xs font-medium ${
                m.trend === "up"
                  ? "text-green-600"
                  : m.trend === "down"
                  ? "text-red-600"
                  : "text-gray-500"
              }`}
            >
              {m.delta}
            </div>
          ) : null}
        </div>
      </div>
    ))}
  </div>
);

export const StatusText = ({ status, text }) => {
  const colors = {
    approved: "text-green-600",
    flagged: "text-red-600",
    reviewing: "text-amber-600",
    normal: "text-gray-600",
    active: "text-green-600",
    pending: "text-amber-600"
  };
  return (
    <div className="flex items-center gap-1.5">
      <div className={`text-[8px] ${colors[status] || "text-gray-500"}`}>●</div>
      <span className="text-xs text-gray-700 capitalize">{text || status}</span>
    </div>
  );
};

export const ScoreText = ({ score }) => {
  let color = "text-green-600";
  if (score > 70) color = "text-red-600";
  else if (score > 30) color = "text-amber-600";
  return <span className={`font-mono ${color}`}>{Math.round(score).toString().padStart(2, "0")}</span>;
};

export const DataTable = ({ columns, data, searchable = false, pagination = false }) => {
  const [sortCol, setSortCol] = useState(null);
  const [sortDir, setSortDir] = useState("asc");
  const [search, setSearch] = useState("");

  const handleSort = (key) => {
    if (sortCol === key) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else {
      setSortCol(key);
      setSortDir("asc");
    }
  };

  let processed = [...data];
  if (search && searchable) {
    processed = processed.filter((row) =>
      Object.values(row).some((val) => String(val).toLowerCase().includes(search.toLowerCase()))
    );
  }
  if (sortCol) {
    processed.sort((a, b) => {
      if (a[sortCol] < b[sortCol]) return sortDir === "asc" ? -1 : 1;
      if (a[sortCol] > b[sortCol]) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden flex flex-col h-full">
      {searchable ? (
        <div className="p-3 border-b border-gray-200 flex items-center gap-2">
          <Search size={14} className="text-gray-400" />
          <input
            type="text"
            placeholder="Buscar..."
            className="text-sm outline-none w-full text-gray-700"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      ) : null}
      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`py-2 px-3 text-[10px] font-medium text-gray-500 uppercase tracking-wider ${
                    col.sortable ? "cursor-pointer hover:bg-gray-100" : ""
                  } ${col.align === "right" ? "text-right" : ""}`}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <div className={`flex items-center gap-1 ${col.align === "right" ? "justify-end" : ""}`}>
                    {col.label}
                    {col.sortable && sortCol === col.key ? (
                      <ArrowUpDown size={10} className={sortDir === "asc" ? "rotate-180" : ""} />
                    ) : null}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="text-xs divide-y divide-gray-100">
            {processed.map((row, i) => (
              <tr key={`${row.id || i}`} className="hover:bg-gray-50 transition-colors">
                {columns.map((col) => (
                  <td
                    key={`${col.key}-${row.id || i}`}
                    className={`py-2 px-3 whitespace-nowrap ${col.align === "right" ? "text-right" : ""}`}
                  >
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pagination ? (
        <div className="p-3 border-t border-gray-200 text-xs text-gray-500 flex justify-between items-center bg-gray-50">
          <span>Mostrando {processed.length} registros</span>
          <div className="flex gap-4">
            <button className="hover:text-gray-900 disabled:opacity-50">← Anterior</button>
            <button className="hover:text-gray-900 disabled:opacity-50">Proxima →</button>
          </div>
        </div>
      ) : null}
    </div>
  );
};
