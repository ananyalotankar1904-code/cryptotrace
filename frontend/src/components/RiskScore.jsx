import RiskIndicatorList from './RiskIndicatorList'
import { displayRiskLevel, riskTone } from '../utils/riskDisplay'

function Meter({ value, label }) {
  const width = Math.max(0, Math.min(100, Number(value) || 0))
  return (
    <div
      className="meter"
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={width}
    >
      <span className="meter__fill" style={{ width: `${width}%` }} />
    </div>
  )
}

function RiskScore({ risk }) {
  if (!risk || (risk.score == null && !risk.level && !risk.indicators?.length)) {
    return (
      <section className="panel">
        <h2 className="panel__title">Risk Analysis</h2>
        <p className="panel__empty">Risk assessment unavailable.</p>
      </section>
    )
  }

  const level = displayRiskLevel(risk.level, risk.score)
  const tone = riskTone(level)
  const breakdown = risk.breakdown || []
  const breakdownTotal = breakdown.reduce((sum, row) => sum + (row.points || 0), 0)

  return (
    <section className={`panel risk-panel risk-panel--${tone}`}>
      <h2 className="panel__title">Risk Score</h2>
      {risk.score != null ? (
        <>
          <p className={`risk-score risk-score--${tone}`}>{risk.score} / 100</p>
          <Meter value={risk.score} label="Risk score" />
        </>
      ) : (
        <p className="panel__empty">Risk assessment unavailable.</p>
      )}
      {level ? (
        <p className={`risk-level risk-level--${tone}`}>{level} RISK</p>
      ) : null}

      <h3 className="subhead">Why is this wallet {level ? `${level.toLowerCase()} risk` : 'scored'}?</h3>
      <p className="panel__hint">
        {risk.summary ||
          'The current risk assessment is based on the configured investigation indicators detected in the traced transaction path. It does not prove criminal activity.'}
      </p>

      <h3 className="subhead">Risk indicators</h3>
      <RiskIndicatorList indicators={risk.indicators} />

      {breakdown.length > 0 ? (
        <>
          <h3 className="subhead">Risk score breakdown</h3>
          <p className="panel__hint">
            Demonstration of a rule-based concept only. Not a validated forensic model.
          </p>
          <table className="breakdown-table">
            <tbody>
              {breakdown.map((row) => (
                <tr key={row.title}>
                  <td>{row.title}</td>
                  <td>+{row.points}</td>
                </tr>
              ))}
              <tr className="breakdown-table__total">
                <td>Total</td>
                <td>{breakdownTotal}</td>
              </tr>
            </tbody>
          </table>
        </>
      ) : null}
    </section>
  )
}

export default RiskScore
