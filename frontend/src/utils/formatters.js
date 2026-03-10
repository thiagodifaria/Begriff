export const formatBRL = (val) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(val || 0));

export const formatNum = (val) => new Intl.NumberFormat("pt-BR").format(Number(val || 0));

export const formatPct = (val) => `${(Number(val || 0) * 100).toFixed(1)}%`;

export const formatShortDate = (isoString) => {
  if (!isoString) return "--";
  const d = new Date(isoString);
  if (Number.isNaN(d.getTime())) return "--";
  return `${d.getDate().toString().padStart(2, "0")}/${(d.getMonth() + 1)
    .toString()
    .padStart(2, "0")} ${d.getHours().toString().padStart(2, "0")}:${d
    .getMinutes()
    .toString()
    .padStart(2, "0")}`;
};

export const truncHash = (hash) => (hash ? `${hash.substring(0, 8)}...` : "--");
