/**
 * Display helper only. Does not calculate or score risk.
 * Uses an explicit label when present; otherwise maps an existing 0–100 score.
 */
export function displayRiskLevel(explicitLevel, score) {
  if (explicitLevel) {
    return String(explicitLevel).toUpperCase()
  }

  if (score == null || Number.isNaN(Number(score))) {
    return null
  }

  const value = Number(score)
  if (value >= 75) return 'CRITICAL'
  if (value >= 50) return 'HIGH'
  if (value >= 25) return 'MEDIUM'
  return 'LOW'
}

export function riskTone(level) {
  const text = String(level || '').toUpperCase()
  if (text === 'CRITICAL') return 'critical'
  if (text === 'HIGH') return 'high'
  if (text === 'MEDIUM') return 'medium'
  if (text === 'LOW') return 'low'
  return 'medium'
}
