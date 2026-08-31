import { riskTone } from '../utils/riskDisplay'

function RiskIndicatorList({ indicators }) {
  if (!indicators || indicators.length === 0) {
    return null
  }

  return (
    <ul className="indicator-list">
      {indicators.map((item) => {
        const title = item.title || item
        const severity = String(item.severity || 'MEDIUM').toUpperCase()
        const tone = riskTone(severity)

        return (
          <li key={title} className={`indicator-item indicator-item--${tone}`}>
            <p className="indicator-item__severity">{severity}</p>
            <p className="indicator-item__title">{title}</p>
            {item.description ? (
              <p className="indicator-item__desc">{item.description}</p>
            ) : null}
          </li>
        )
      })}
    </ul>
  )
}

export default RiskIndicatorList
