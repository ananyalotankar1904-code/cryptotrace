import { displayRiskLevel, riskTone } from '../utils/riskDisplay'

function RiskReadout({ score, level }) {
  const text = displayRiskLevel(level, score)

  if (score == null && !text) {
    return null
  }

  const tone = riskTone(text)

  return (
    <div className={`risk-readout risk-readout--${tone}`}>
      <p className="detail-row__label">Risk</p>
      {score != null ? (
        <p className="risk-readout__score">{score} / 100</p>
      ) : null}
      {text ? <p className="risk-readout__level">{text} RISK</p> : null}
    </div>
  )
}

export default RiskReadout
