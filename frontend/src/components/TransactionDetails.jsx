import AddressDisplay from './AddressDisplay'
import DetailRow from './DetailRow'
import DetailsPanel from './DetailsPanel'
import { displayRiskLevel, riskTone } from '../utils/riskDisplay'
import { formatTimestamp } from '../utils/formatTimestamp'

function hopLabel(transaction) {
  if (transaction.hop == null) {
    return null
  }
  if (transaction.totalHops != null) {
    return `${transaction.hop} of ${transaction.totalHops}`
  }
  return String(transaction.hop)
}

function TransactionDetails({ transaction, onClose }) {
  if (!transaction) {
    return null
  }

  if (!transaction.source && !transaction.target && !transaction.id) {
    return (
      <DetailsPanel title="Transaction Details" onClose={onClose}>
        <p className="panel__empty">Transaction information could not be found.</p>
      </DetailsPanel>
    )
  }

  const when = formatTimestamp(transaction.timestamp)
  const riskText = displayRiskLevel(transaction.risk)
  const hop = hopLabel(transaction)

  return (
    <DetailsPanel title="Transaction Details" onClose={onClose}>
      <div className="tx-flow" aria-label="Transaction direction">
        <p className="tx-flow__label">From</p>
        <AddressDisplay address={transaction.source} />
        <p className="tx-flow__arrow" aria-hidden="true">
          ↓
        </p>
        <p className="tx-flow__label">To</p>
        <AddressDisplay address={transaction.target} />
      </div>

      <p className="tx-amount">
        {transaction.amount != null ? (
          <>
            {transaction.amount} {transaction.token}
          </>
        ) : (
          'Details unavailable'
        )}
      </p>

      <dl className="details-dl">
        <DetailRow label="Token">{transaction.token}</DetailRow>
        {when ? (
          <DetailRow label="Timestamp">
            {when.date}
            {when.time ? (
              <>
                <br />
                {when.time}
              </>
            ) : null}
          </DetailRow>
        ) : null}
        <DetailRow label="Hop">{hop}</DetailRow>
        {transaction.txHash ? (
          <DetailRow label="Transaction Hash">
            <AddressDisplay address={transaction.txHash} showFull />
          </DetailRow>
        ) : null}
        <DetailRow label="Block">{transaction.block}</DetailRow>
        <DetailRow label="Status">{transaction.status}</DetailRow>
        {riskText ? (
          <DetailRow label="Risk">
            <span className={`risk-chip risk-chip--${riskTone(riskText)}`}>
              {riskText}
            </span>
          </DetailRow>
        ) : null}
      </dl>

      <button type="button" className="btn btn--secondary explorer-btn" disabled>
        VIEW ON EXPLORER
      </button>
      <p className="details-footnote">
        Explorer links are not enabled for demonstration data. This control is
        reserved for a future live-chain integration.
      </p>
    </DetailsPanel>
  )
}

export default TransactionDetails
