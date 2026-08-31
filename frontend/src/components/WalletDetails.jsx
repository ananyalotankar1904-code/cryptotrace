import AddressDisplay from './AddressDisplay'
import DetailRow from './DetailRow'
import DetailsPanel from './DetailsPanel'
import RiskReadout from './RiskReadout'
import { formatTimestamp } from '../utils/formatTimestamp'

function typeHeading(wallet) {
  if (wallet.type === 'exchange') return 'Entity Details'
  if (wallet.type === 'suspect') return 'Suspect Wallet'
  if (wallet.type === 'contract') return 'Smart Contract'
  return 'Wallet Details'
}

function typeLabel(wallet) {
  if (wallet.walletType) return wallet.walletType
  if (wallet.type === 'exchange') return 'Exchange / VASP'
  if (wallet.type === 'suspect') return 'Suspect Wallet'
  if (wallet.type === 'contract') return 'Smart Contract'
  return 'Wallet'
}

function WalletDetails({ wallet, onClose }) {
  if (!wallet) {
    return null
  }

  if (!wallet.address) {
    return (
      <DetailsPanel title="Wallet Details" onClose={onClose}>
        <p className="panel__empty">Wallet information could not be found.</p>
      </DetailsPanel>
    )
  }

  const isExchange = wallet.type === 'exchange'
  const firstSeen = formatTimestamp(wallet.firstSeen)

  return (
    <DetailsPanel title={typeHeading(wallet)} onClose={onClose}>
      <dl className="details-dl">
        {isExchange ? (
          <DetailRow label="Entity">{wallet.label || wallet.knownEntity}</DetailRow>
        ) : null}

        <DetailRow label="Address">
          <AddressDisplay address={wallet.address} showFull />
        </DetailRow>

        <DetailRow label="Type">{typeLabel(wallet)}</DetailRow>
        <DetailRow label="Status">{wallet.status}</DetailRow>
        <DetailRow label="Chain">{wallet.chain}</DetailRow>
        <DetailRow label="Transactions">{wallet.transactionCount}</DetailRow>
        {firstSeen ? (
          <DetailRow label="First Seen">
            {firstSeen.date}
            {firstSeen.time ? ` · ${firstSeen.time}` : ''}
          </DetailRow>
        ) : null}
        <DetailRow label="Known Entity">{wallet.knownEntity || 'Unknown'}</DetailRow>

        {isExchange ? (
          <>
            {wallet.confidence != null ? (
              <DetailRow label="Attribution confidence">{wallet.confidence}%</DetailRow>
            ) : (
              <DetailRow label="Attribution confidence">Confidence unavailable</DetailRow>
            )}
            {wallet.destinationHop != null ? (
              <DetailRow label="Hop">{wallet.destinationHop}</DetailRow>
            ) : null}
          </>
        ) : wallet.riskScore != null || wallet.riskLevel || wallet.indicators?.length ? (
          <>
            <RiskReadout score={wallet.riskScore} level={wallet.riskLevel} />
            {wallet.indicators?.length ? (
              <DetailRow label="Indicators">
                <ul className="wallet-indicator-names">
                  {wallet.indicators.map((item) => (
                    <li key={item.title || item}>{item.title || item}</li>
                  ))}
                </ul>
              </DetailRow>
            ) : null}
          </>
        ) : (
          <p className="panel__empty">Risk assessment unavailable.</p>
        )}
      </dl>

      {isExchange ? (
        <p className="details-footnote">
          VASP identification indicates a potential service destination and does
          not by itself identify an individual or establish criminal wrongdoing.
        </p>
      ) : null}
    </DetailsPanel>
  )
}

export default WalletDetails
