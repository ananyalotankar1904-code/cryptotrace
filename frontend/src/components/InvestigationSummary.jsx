import { getInvestigationRisk, getVaspState } from '../utils/investigationView'
import { displayRiskLevel } from '../utils/riskDisplay'

function InvestigationSummary({ investigation }) {
  const risk = getInvestigationRisk(investigation)
  const vasp = investigation.vasp
  const vaspState = getVaspState(vasp)
  const level = displayRiskLevel(risk?.level, risk?.score)

  let vaspLabel = 'None identified'
  if (vaspState === 'identified') vaspLabel = vasp.name
  if (vaspState === 'possible') vaspLabel = `${vasp.name} (requires verification)`

  return (
    <section className="panel investigation-summary">
      <h2 className="panel__title">Investigation Summary</h2>
      <dl className="summary-facts">
        <div>
          <dt>Risk</dt>
          <dd>{level ? `${level}` : 'Unavailable'}</dd>
        </div>
        <div>
          <dt>VASP</dt>
          <dd>{vaspLabel}</dd>
        </div>
        <div>
          <dt>Attribution confidence</dt>
          <dd>
            {vasp?.confidence != null ? `${vasp.confidence}%` : 'Confidence unavailable'}
          </dd>
        </div>
        <div>
          <dt>Hops</dt>
          <dd>{investigation.hops ?? '—'}</dd>
        </div>
      </dl>
      {risk?.summary ? (
        <p className="investigation-summary__concern">
          <strong>Primary concern. </strong>
          {risk.summary}
        </p>
      ) : null}
    </section>
  )
}

export default InvestigationSummary
