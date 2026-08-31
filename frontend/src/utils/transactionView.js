export function transactionEdgeId(tx) {
  return `tx-${tx.id}`
}

export function toDetailsTransaction(tx, hops) {
  if (!tx) {
    return null
  }

  return {
    id: tx.id != null ? transactionEdgeId(tx) : tx.source ? `tx-unknown` : undefined,
    source: tx.from || tx.source,
    target: tx.to || tx.target,
    from: tx.from || tx.source,
    to: tx.to || tx.target,
    amount: tx.amount,
    token: tx.token,
    timestamp: tx.timestamp,
    hop: tx.hop,
    totalHops: hops ?? tx.totalHops,
    risk: tx.risk,
    txHash: tx.txHash || tx.hash,
    block: tx.block,
    status: tx.status,
    label: `${tx.amount} ${tx.token}`,
  }
}

export function uniqueTokens(transactions) {
  return [...new Set((transactions || []).map((tx) => tx.token).filter(Boolean))].sort()
}

export function uniqueHops(transactions) {
  return [...new Set((transactions || []).map((tx) => tx.hop).filter((hop) => hop != null))]
    .sort((a, b) => a - b)
}

function matchesSearch(tx, query) {
  if (!query) {
    return true
  }
  const from = String(tx.from || '').toLowerCase()
  const to = String(tx.to || '').toLowerCase()
  const hash = String(tx.txHash || tx.hash || '').toLowerCase()
  return from.includes(query) || to.includes(query) || hash.includes(query)
}

export function filterTransactions(transactions, filters, vaspAddress) {
  const search = String(filters.searchTerm || '').trim().toLowerCase()
  const token = filters.selectedToken || 'all'
  const hop = filters.selectedHop || 'all'
  const risk = String(filters.selectedRisk || 'all').toLowerCase()
  const vasp = filters.selectedVasp || 'all'

  return (transactions || []).filter((tx) => {
    if (token !== 'all' && tx.token !== token) {
      return false
    }
    if (hop !== 'all' && Number(tx.hop) !== Number(hop)) {
      return false
    }
    if (risk !== 'all' && String(tx.risk || '').toLowerCase() !== risk) {
      return false
    }
    if (vasp === 'vasp' && vaspAddress) {
      if (tx.to !== vaspAddress && tx.from !== vaspAddress) {
        return false
      }
    }
    return matchesSearch(tx, search)
  })
}

const RISK_RANK = {
  low: 1,
  medium: 2,
  high: 3,
  critical: 4,
}

export function sortTransactions(transactions, field, direction) {
  const dir = direction === 'desc' ? -1 : 1
  return [...transactions].sort((a, b) => {
    let cmp = 0
    if (field === 'amount') {
      cmp = Number(a.amount) - Number(b.amount)
    } else if (field === 'hop') {
      cmp = Number(a.hop || 0) - Number(b.hop || 0)
    } else if (field === 'risk') {
      cmp = (RISK_RANK[String(a.risk).toLowerCase()] || 0)
        - (RISK_RANK[String(b.risk).toLowerCase()] || 0)
    } else {
      cmp = String(a.timestamp || '').localeCompare(String(b.timestamp || ''))
    }
    if (cmp === 0) {
      cmp = Number(a.id || 0) - Number(b.id || 0)
    }
    return cmp * dir
  })
}
