import { useState } from 'react'
import { formatAddress } from '../utils/formatAddress'

function AddressDisplay({
  address,
  className = '',
  showFull = false,
  copyLabel = 'Copy',
}) {
  const [copied, setCopied] = useState(false)

  if (!address) {
    return <span className="address-display">Details unavailable</span>
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(address)
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch {
      setCopied(false)
    }
  }

  return (
    <span className={`address-display ${className}`.trim()}>
      <code className="address-display__short" title={address}>
        {formatAddress(address)}
      </code>
      <button
        type="button"
        className="address-display__copy"
        onClick={handleCopy}
        aria-label={`Copy ${address}`}
      >
        {copied ? 'Copied!' : copyLabel}
      </button>
      {showFull ? (
        <code className="address-display__full">{address}</code>
      ) : null}
    </span>
  )
}

export default AddressDisplay
