import { formatAddress } from './formatAddress.js'

function inferType(address, investigation) {
  const meta = investigation.entityMeta?.[address]
  if (meta?.type) {
    return meta.type
  }

  if (address === investigation.suspectWallet) {
    return 'suspect'
  }

  const pathNode = investigation.path?.find((item) => item.address === address)
  if (pathNode && /vasp|binance|exchange/i.test(pathNode.label)) {
    return 'exchange'
  }

  if (investigation.vasp && pathNode && pathNode === investigation.path.at(-1)) {
    return 'exchange'
  }

  return 'wallet'
}

function buildDisplayLabel(node) {
  if (node.type === 'exchange') {
    return `${node.label}\nExchange`
  }
  if (node.type === 'suspect') {
    return `Suspect\n${formatAddress(node.address)}`
  }
  if (node.type === 'contract') {
    return `${node.label}\n${formatAddress(node.address)}`
  }
  if (node.label && !node.label.startsWith('0x')) {
    return `${node.label}\n${formatAddress(node.address)}`
  }
  return formatAddress(node.address)
}

/**
 * Converts investigation transactions into graph nodes and edges.
 * Later, a backend can skip this and pass nodes/edges directly.
 */
export function buildGraphFromInvestigation(investigation) {
  if (!investigation) {
    return { nodes: [], edges: [], moneyPathNodeIds: [], moneyPathEdgeIds: [] }
  }

  const transactions = investigation.transactions || []
  const counts = {}

  transactions.forEach((tx) => {
    counts[tx.from] = (counts[tx.from] || 0) + 1
    counts[tx.to] = (counts[tx.to] || 0) + 1
  })

  const addressSet = new Set()
  transactions.forEach((tx) => {
    addressSet.add(tx.from)
    addressSet.add(tx.to)
  })

  const nodes = Array.from(addressSet).map((address) => {
    const meta = investigation.entityMeta?.[address] || {}
    const type = inferType(address, investigation)
    const relatedTimes = transactions
      .filter((tx) => tx.from === address || tx.to === address)
      .map((tx) => tx.timestamp)
      .filter(Boolean)
      .sort()

    const node = {
      id: address,
      address,
      type,
      label: meta.label || (type === 'suspect' ? 'Suspect' : formatAddress(address)),
      walletType: meta.walletType || (type === 'exchange' ? 'Exchange / VASP' : type === 'contract' ? 'Smart Contract' : type === 'suspect' ? 'Suspect Wallet' : 'Wallet'),
      status: meta.status || (type === 'suspect' ? 'Under Investigation' : type === 'contract' ? 'Contract Address' : 'Unknown'),
      riskScore: meta.riskScore,
      riskLevel: meta.riskLevel,
      indicators: meta.indicators || [],
      knownEntity: meta.knownEntity || 'Unknown',
      confidence: type === 'exchange' ? (meta.confidence ?? investigation.vasp?.confidence) : meta.confidence,
      destinationHop: type === 'exchange'
        ? (investigation.vasp?.hop ?? investigation.vasp?.finalDestinationHop)
        : undefined,
      transactionCount: counts[address] || 0,
      chain: investigation.chain,
      firstSeen: relatedTimes[0] || null,
    }
    node.displayLabel = buildDisplayLabel(node)
    return node
  })

  const edges = transactions.map((tx) => ({
    id: `tx-${tx.id}`,
    source: tx.from,
    target: tx.to,
    amount: tx.amount,
    token: tx.token,
    label: `${tx.amount} ${tx.token}`,
    timestamp: tx.timestamp,
    hop: tx.hop,
    totalHops: investigation.hops,
    risk: tx.risk,
    txHash: tx.txHash,
    block: tx.block,
    status: tx.status,
  }))

  const moneyPathNodeIds = (investigation.path || [])
    .map((item) => item.address)
    .filter((address) => addressSet.has(address))

  const pathPairs = new Set()
  for (let i = 0; i < moneyPathNodeIds.length - 1; i += 1) {
    pathPairs.add(`${moneyPathNodeIds[i]}->${moneyPathNodeIds[i + 1]}`)
  }

  const moneyPathEdgeIds = edges
    .filter((edge) => pathPairs.has(`${edge.source}->${edge.target}`))
    .map((edge) => edge.id)

  return { nodes, edges, moneyPathNodeIds, moneyPathEdgeIds }
}

// ─── Backend graph adapter ────────────────────────────────────────────────────
/**
 * Build graph data directly from the backend's pre-computed graph payload
 * (investigation._backendGraph). This avoids re-deriving the graph from
 * transactions and uses the analytics engine's own topology.
 *
 * Backend node schema:
 *   { id, type, hop, known_entity, entity_type }
 *
 * Backend edge schema:
 *   { source, target, asset, value, transaction_hash, timestamp, block_number, category, hop }
 *
 * Output matches TransactionGraph.jsx's expected props:
 *   nodes[]  — Cytoscape node data objects
 *   edges[]  — Cytoscape edge data objects
 *   moneyPathNodeIds[] — addresses on the highlighted money path
 *   moneyPathEdgeIds[] — edge ids on the highlighted money path
 */
export function buildGraphFromBackend(investigation) {
  if (!investigation?._backendGraph) {
    return buildGraphFromInvestigation(investigation)
  }

  const backendNodes = investigation._backendGraph.nodes ?? []
  const backendEdges = investigation._backendGraph.edges ?? []

  if (backendNodes.length === 0) {
    // Backend returned an empty graph — fall back to transaction-derived graph
    return buildGraphFromInvestigation(investigation)
  }

  const suspectAddr = (investigation.suspectWallet ?? '').toLowerCase()
  const vaspAddr    = (investigation.vasp?.address   ?? '').toLowerCase()

  // ── Nodes ────────────────────────────────────────────────────────────────
  const nodeAddressSet = new Set(backendNodes.map((n) => n.id))

  const nodes = backendNodes.map((n) => {
    // Determine node type — prefer backend value, enrich with VASP match
    let type = n.type ?? 'wallet'
    if (n.id === suspectAddr) type = 'suspect'
    else if (vaspAddr && n.id === vaspAddr) type = 'exchange'
    else if (n.known_entity) type = 'exchange'

    const knownEntityLabel = n.known_entity ?? null
    const label =
      type === 'suspect'
        ? 'Suspect'
        : knownEntityLabel
        ? knownEntityLabel
        : formatAddress(n.id)

    const walletType =
      type === 'exchange'
        ? 'Exchange / VASP'
        : type === 'suspect'
        ? 'Suspect Wallet'
        : 'Wallet'

    const status =
      type === 'suspect'
        ? 'Under Investigation'
        : knownEntityLabel
        ? `Known entity · ${n.entity_type ?? 'VASP'}`
        : 'Unknown'

    const node = {
      id:             n.id,
      address:        n.id,
      type,
      label,
      walletType,
      status,
      hop:            n.hop ?? null,
      knownEntity:    knownEntityLabel ?? 'Unknown',
      confidence:     type === 'exchange' ? investigation.vasp?.confidence : undefined,
      destinationHop: type === 'exchange' ? (n.hop ?? investigation.vasp?.hop) : undefined,
      transactionCount: 0, // enriched below
      chain:          investigation.chain ?? 'ethereum',
      riskScore:      null,
      riskLevel:      null,
      indicators:     [],
      firstSeen:      null,
    }
    node.displayLabel = buildDisplayLabel(node)
    return node
  })

  // ── Edges ─────────────────────────────────────────────────────────────────
  // Backend may produce multiple edges between the same pair (MultiDiGraph).
  // We give each a unique id using the transaction_hash.
  const txCountPerNode = {}

  const edges = backendEdges.map((e, index) => {
    const hash   = e.transaction_hash ?? ''
    const edgeId = hash ? `tx-${hash}` : `tx-edge-${index}`
    const amount = e.value  ?? null
    const token  = e.asset  ?? 'ETH'

    // Accumulate transaction counts per node
    if (e.source) txCountPerNode[e.source] = (txCountPerNode[e.source] || 0) + 1
    if (e.target) txCountPerNode[e.target] = (txCountPerNode[e.target] || 0) + 1

    return {
      id:        edgeId,
      source:    e.source,
      target:    e.target,
      amount,
      token,
      label:     amount != null ? `${amount} ${token}` : token,
      timestamp: e.timestamp    ?? null,
      hop:       e.hop          ?? null,
      totalHops: investigation.hops,
      txHash:    hash || null,
      block:     e.block_number ?? null,
      category:  e.category     ?? null,
      status:    null,
      risk:      null,
    }
  })

  // Patch transaction counts back onto nodes
  nodes.forEach((node) => {
    node.transactionCount = txCountPerNode[node.id] || 0
  })

  // ── Money path highlight ──────────────────────────────────────────────────
  // Build from investigation.path (VASP path) if available
  const pathAddresses = (investigation.path ?? [])
    .map((item) => (typeof item === 'string' ? item : item.address))
    .filter((addr) => nodeAddressSet.has(addr))

  const pathPairSet = new Set()
  for (let i = 0; i < pathAddresses.length - 1; i += 1) {
    pathPairSet.add(`${pathAddresses[i]}->${pathAddresses[i + 1]}`)
  }

  const moneyPathEdgeIds = edges
    .filter((edge) => pathPairSet.has(`${edge.source}->${edge.target}`))
    .map((edge) => edge.id)

  return {
    nodes,
    edges,
    moneyPathNodeIds: pathAddresses,
    moneyPathEdgeIds,
  }
}
