function safeNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function deriveTransactions(analyses) {
  const rows = [];

  analyses.forEach((analysis) => {
    const results = analysis.analysis_results || {};
    const riskiest = results.fraud_analysis?.riskiest_transactions || [];
    const carbonBreakdown = results.carbon_analysis?.breakdown_by_category || {};
    const defaultCarbon = Object.values(carbonBreakdown).reduce((acc, val) => acc + safeNumber(val), 0);

    if (riskiest.length === 0) {
      rows.push({
        id: `ANL-${analysis.id}`,
        amount: safeNumber(results.summary?.total_amount),
        description: `Analise ${analysis.id}`,
        category: "analise",
        merchant: "motor-analitico",
        riskScore: Math.round(safeNumber(results.fraud_analysis?.highest_risk_score) * 100),
        carbonKg: defaultCarbon,
        status: results.fraud_analysis?.fraud_detected ? "reviewing" : "approved",
        timestamp: analysis.created_at,
        fraudScore: safeNumber(results.fraud_analysis?.highest_risk_score),
        auditHash: `analysis-${analysis.id}`,
        bank: analysis.sourceType || "N/A"
      });
      return;
    }

    riskiest.forEach((tx, index) => {
      rows.push({
        id: tx.id || `ANL-${analysis.id}-${index + 1}`,
        amount: safeNumber(tx.amount),
        description: tx.description || `Transacao derivada da analise ${analysis.id}`,
        category: tx.category || "outros",
        merchant: tx.merchant || tx.description || "N/A",
        riskScore: Math.round(safeNumber(tx.risk_score) * 100),
        carbonKg: safeNumber(carbonBreakdown[tx.category]) || 0,
        status: safeNumber(tx.risk_score) > 0.7 ? "flagged" : "reviewing",
        timestamp: tx.timestamp || tx.transaction_date || analysis.created_at,
        fraudScore: safeNumber(tx.risk_score),
        auditHash: `analysis-${analysis.id}-${index}`,
        bank: analysis.sourceType || "N/A"
      });
    });
  });

  return rows.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

function deriveVolumeChart(analyses) {
  const buckets = new Map();
  analyses.forEach((analysis) => {
    const date = new Date(analysis.created_at);
    const key = `${date.getHours().toString().padStart(2, "0")}:00`;
    const entry = buckets.get(key) || { time: key, aprovadas: 0, sinalizadas: 0 };
    entry.aprovadas += safeNumber(analysis.analysis_results?.summary?.total_transactions);
    entry.sinalizadas += safeNumber(
      analysis.analysis_results?.fraud_analysis?.transactions_above_threshold
    );
    buckets.set(key, entry);
  });
  return [...buckets.values()].sort((a, b) => a.time.localeCompare(b.time));
}

function derivePieCategory(analyses) {
  const categoryTotals = new Map();
  analyses.forEach((analysis) => {
    const breakdown = analysis.analysis_results?.carbon_analysis?.breakdown_by_category || {};
    Object.entries(breakdown).forEach(([category, value]) => {
      categoryTotals.set(category, (categoryTotals.get(category) || 0) + safeNumber(value));
    });
  });
  return [...categoryTotals.entries()]
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);
}

function deriveFraudAlerts(transactions) {
  return transactions
    .filter((tx) => tx.fraudScore >= 0.45)
    .slice(0, 8)
    .map((tx) => ({
      id: tx.id,
      amount: tx.amount,
      type: tx.category || "Alerta",
      score: tx.fraudScore,
      time: tx.timestamp,
      status: tx.fraudScore > 0.7 ? "pending" : "investigating"
    }));
}

function deriveScatter(transactions) {
  return transactions.slice(0, 120).map((tx) => ({
    x: safeNumber(tx.amount),
    y: safeNumber(tx.fraudScore),
    type: tx.fraudScore > 0.7 ? "anomaly" : "normal"
  }));
}

function deriveRadar(transactions) {
  const avgRisk = transactions.length
    ? transactions.reduce((acc, tx) => acc + safeNumber(tx.fraudScore), 0) / transactions.length
    : 0;
  const anomalyRatio = transactions.length
    ? transactions.filter((tx) => tx.fraudScore > 0.7).length / transactions.length
    : 0;

  return [
    { subject: "Velocity", normal: 30, anomaly: Math.min(100, Math.round(anomalyRatio * 100) + 20) },
    { subject: "Valor", normal: 40, anomaly: Math.min(100, Math.round(avgRisk * 100) + 25) },
    { subject: "Distancia", normal: 20, anomaly: Math.min(100, Math.round(avgRisk * 100) + 30) },
    { subject: "Frequencia", normal: 50, anomaly: Math.min(100, Math.round(anomalyRatio * 100) + 15) },
    { subject: "Horario", normal: 10, anomaly: Math.min(100, Math.round(avgRisk * 100) + 35) },
    { subject: "Dispositivo", normal: 5, anomaly: Math.min(100, Math.round(anomalyRatio * 100) + 25) }
  ];
}

function deriveProjection(analyses) {
  const sorted = [...analyses].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );
  let running = 0;
  return sorted.slice(0, 12).map((analysis, index) => {
    running += safeNumber(analysis.analysis_results?.summary?.total_amount);
    const base = Math.round((running / 1000000) * 10) / 10;
    return {
      month: `M${index + 1}`,
      base,
      otimista: Math.round(base * 1.15 * 10) / 10,
      pessimista: Math.round(base * 0.8 * 10) / 10
    };
  });
}

function deriveLogs(analyses) {
  return analyses.slice(0, 20).map((analysis) => {
    const total = safeNumber(analysis.analysis_results?.summary?.total_transactions);
    const highRisk = safeNumber(analysis.analysis_results?.fraud_analysis?.transactions_above_threshold);
    const level = highRisk > 0 ? "WARN" : "INFO";
    return {
      time: new Date(analysis.created_at).toISOString().split("T")[1].split(".")[0],
      level,
      msg: `[ANALYSIS] id=${analysis.id} processed=${total} high_risk=${highRisk}`
    };
  });
}

export function buildUiData(analyses) {
  const transactions = deriveTransactions(analyses);
  const totalTransactions = analyses.reduce(
    (acc, item) => acc + safeNumber(item.analysis_results?.summary?.total_transactions),
    0
  );
  const totalAmount = analyses.reduce(
    (acc, item) => acc + safeNumber(item.analysis_results?.summary?.total_amount),
    0
  );
  const highestRisk = analyses.reduce(
    (acc, item) => Math.max(acc, safeNumber(item.analysis_results?.fraud_analysis?.highest_risk_score)),
    0
  );
  const totalCarbon = analyses.reduce(
    (acc, item) => acc + safeNumber(item.analysis_results?.carbon_analysis?.total_carbon_kg),
    0
  );

  return {
    analyses,
    transactions,
    chartVol: deriveVolumeChart(analyses),
    pieCategory: derivePieCategory(analyses),
    fraudAlerts: deriveFraudAlerts(transactions),
    scatterFraud: deriveScatter(transactions),
    radarFeatures: deriveRadar(transactions),
    simProjection: deriveProjection(analyses),
    logs: deriveLogs(analyses),
    metrics: {
      totalTransactions,
      totalAmount,
      highestRisk,
      totalCarbon
    }
  };
}
