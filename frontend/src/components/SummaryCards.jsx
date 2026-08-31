import { getInvestigationRisk, getVaspState } from '../utils/investigationView'
import { displayRiskLevel, riskTone } from '../utils/riskDisplay'

function SummaryCard({ label, value, detail, tone }) {
  return (
    <article className={`summary-card ${tone ? `summary-card--${tone}` : ''}`}>
      <p className="summary-card__label">{label}</p>
      <p className="summary-card__value">{value}</p>
      {detail ? <p className="summary-card__detail">{detail}</p> : null}
    </article>
  )
}

function SummaryCards({ investigation }) {
  const risk = getInvestigationRisk(investigation)
  const level = displayRiskLevel(risk?.level, risk?.score)
  const vaspState = getVaspState(investigation.vasp)
  let vaspValue = 'None'
  let vaspDetail = 'No known VASP'
  if (vaspState === 'identified') {
    vaspValue = investigation.vasp.name
    vaspDetail = 'Identified'
  } else if (vaspState === 'possible') {
    vaspValue = investigation.vasp.name
    vaspDetail = 'Requires verification'
  }

  return (
    <section className="summary-grid" aria-label="Investigation summary">
      <SummaryCard
        label="Risk Score"
        value={risk?.score != null ? `${risk.score} / 100` : '—'}
        detail={level ? `${level} RISK` : 'Unavailable'}
        tone={riskTone(level)}
      />
      <SummaryCard
        label="Total Transactions"
        value={investigation.transactionsCount}
        detail={investigation.chain}
      />
      <SummaryCard
        label="Number of Hops"
        value={investigation.hops}
        detail="Wallets traced"
      />
      <SummaryCard
        label="VASP Status"
        value={vaspValue}
        detail={vaspDetail}
      />
      <SummaryCard
        label="Total Value Traced"
        value={`${investigation.totalValue} ${investigation.totalValueToken}`}
        detail={investigation.isDemo ? 'Demo values' : `Estimated (${investigation.totalValueToken})`}
      />
    </section>
  )
}

export default SummaryCards
