import { displayRiskLevel } from './riskDisplay'

export function confidencePercent(value) {
  if (value == null || value === '') {
    return null
  }
  const number = Number(value)
  if (Number.isNaN(number)) {
    return null
  }
  return number <= 1 ? Math.round(number * 100) : Math.round(number)
}

export function confidenceBand(percent) {
  if (percent == null) {
    return null
  }
  if (percent <= 49) return 'Low'
  if (percent <= 79) return 'Moderate'
  return 'High'
}

export function getVaspState(vasp) {
  if (!vasp || vasp.identified === false && !vasp.possible && !vasp.name) {
    return 'none'
  }
  const percent = confidencePercent(vasp.confidence)
  const status = String(vasp.status || '').toLowerCase()
  const uncertain =
    vasp.possible ||
    status.includes('verification') ||
    status.includes('possible') ||
    (percent != null && percent < 80)

  if (uncertain) {
    return 'possible'
  }
  if (vasp.identified === false && !vasp.name) {
    return 'none'
  }
  return 'identified'
}

export function getInvestigationRisk(investigation) {
  if (!investigation) {
    return null
  }

  const nested = investigation.risk || {}
  const score = nested.score ?? investigation.riskScore
  const level = nested.level ?? investigation.riskLevel

  if (score == null && !level && !nested.indicators && !investigation.riskIndicators) {
    return null
  }

  const indicators = nested.indicators ||
    (investigation.riskIndicators || []).map((item) => (
      typeof item === 'string'
        ? { title: item, severity: level || 'MEDIUM' }
        : item
    ))

  return {
    score,
    level: level || displayRiskLevel(null, score),
    indicators,
    breakdown: nested.breakdown || [],
    summary: nested.summary || '',
  }
}
