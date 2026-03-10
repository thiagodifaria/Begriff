import { useCallback, useEffect, useMemo, useState } from "react";

import { getAnalysisHistory, getBankingAnalysisHistory } from "../services/api";
import { buildUiData } from "../utils/selectors";

export function useUiData(token) {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const [csvHistory, bankingHistory] = await Promise.all([
        getAnalysisHistory(token),
        getBankingAnalysisHistory(token)
      ]);
      const merged = [
        ...(csvHistory || []).map((item) => ({ ...item, sourceType: "csv" })),
        ...(bankingHistory || []).map((item) => ({ ...item, sourceType: "banking" }))
      ].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setAnalyses(merged);
    } catch (err) {
      setError(err.message || "Erro ao carregar dados da plataforma.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    reload();
  }, [reload]);

  const uiData = useMemo(() => buildUiData(analyses), [analyses]);

  return {
    uiData,
    loading,
    error,
    reload
  };
}
