import AddressDisplay from './AddressDisplay'
import { formatTimestamp } from '../utils/formatTimestamp'
import { displayRiskLevel, riskTone } from '../utils/riskDisplay'

function TransactionTimeline({
  transactions,
  selectedId,
  onSelect,
}) {
  return (
    <section className="panel">
      <h2 className="panel__title">Fund Movement Timeline</h2>
      <p className="panel__hint">
        Chronological demonstration events. Click an event to open transaction
        details. This is mock data, not live chain activity.
      </p>

      {transactions.length === 0 ? (
        <div className="empty-filter-state">
          <p className="empty-filter-state__title">No transactions found</p>
          <p className="panel__empty">
            No transactions match the current filters.
          </p>
        </div>
      ) : (
        <ol className="timeline">
          {transactions.map((tx) => {
            const when = formatTimestamp(tx.timestamp)
            const risk = displayRiskLevel(tx.risk)
            const selected =
              selectedId === `tx-${tx.id}` ||
              selectedId === String(tx.id) ||
              selectedId === tx.id

            return (
              <li key={tx.id}>
            <article
                  className={`timeline-event ${selected ? 'is-selected' : ''}`}
                  onClick={() => onSelect(tx)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault()
                      onSelect(tx)
                    }
                  }}
                  tabIndex={0}
                  role="button"
                >
                  <p className="timeline-event__hop">Hop {tx.hop}</p>
                  <p className="timeline-event__time">
                    {when ? `${when.date} • ${when.time || ''}` : tx.timestamp}
                  </p>
                  <div className="timeline-event__flow">
                    <AddressDisplay address={tx.from} />
                    <span aria-hidden="true">↓</span>
                    <AddressDisplay address={tx.to} />
                  </div>
                  <p className="timeline-event__amount">
                    {tx.amount} {tx.token}
                  </p>
                  {risk ? (
                    <p className={`risk-chip risk-chip--${riskTone(risk)}`}>
                      {risk}
                    </p>
                  ) : null}
                </article>
              </li>
            )
          })}
        </ol>
      )}
    </section>
  )
}

export default TransactionTimeline
