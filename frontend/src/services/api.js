/**
 * Frontend API layer — CryptoTrace
 *
 * traceWallet(address) is the ONLY public function Dashboard.jsx calls.
 *
 * Behaviour:
 *  - Demo wallet addresses  → return mock investigation (no backend call)
 *  - All other addresses    → call GET /wallet/{address}/analyze on the
 *                             real FastAPI backend, adapt the response, and
 *                             perform VASP matching with the local dataset.
 *
 * Environment variable:
 *   VITE_API_BASE_URL  e.g. http://localhost:8000
 *   (set in frontend/.env — falls back to empty string → relative path)
 */

import {
  DEMO_WALLET,
  NO_VASP_DEMO_WALLET,
  POSSIBLE_VASP_DEMO_WALLET,
  demoInvestigation,
  noVaspInvestigation,
  possibleVaspInvestigation,
} from '../data/mockData'

// Removed matchVaspFromTransactions since backend now handles it natively
// ─── Config ──────────────────────────────────────────────────────────────────

const API_BASE =
  typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL
    ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')
    : ''

// ─── Helpers ─────────────────────────────────────────────────────────────────

function normalizeAddress(address) {
  return String(address || '').trim().toLowerCase()
}

// ─── Transaction adapter ─────────────────────────────────────────────────────

/**
 * Map one backend transaction record (snake_case) → frontend transaction (camelCase).
 * Preserves: timestamp, hop, category, contract_address.
 * Does NOT invent values that are absent in the backend record.
 */
function adaptTransaction(raw, index) {
  return {
    // identity — use index as fallback id so graphUtils can build edges
    id: index,

    // address mapping
    from: raw.from_address ?? raw.from ?? null,
    to:   raw.to_address   ?? raw.to   ?? null,

    // value mapping
    amount: raw.value  ?? raw.amount ?? null,
    token:  raw.asset  ?? raw.token  ?? null,

    // block / hash
    txHash: raw.transaction_hash ?? raw.txHash ?? null,
    block:  raw.block_number     ?? raw.block  ?? null,

    // preserved as-is
    timestamp:        raw.timestamp        ?? null,
    hop:              raw.hop              ?? null,
    category:         raw.category        ?? null,
    contract_address: raw.contract_address ?? null,

    // status is not returned by the backend tracer — omit rather than invent
    status: raw.status ?? null,
    risk:   raw.risk   ?? null,
  }
}

// ─── Risk adapter ─────────────────────────────────────────────────────────────

/**
 * Map backend risk_analysis object → frontend risk shape consumed by
 * getInvestigationRisk() in investigationView.js.
 */
function adaptRisk(riskAnalysis) {
  if (!riskAnalysis) return null

  const rawIndicators = riskAnalysis.risk_indicators ?? []
  const rawDetails    = riskAnalysis.risk_indicator_details ?? []

  // Normalise indicators to the { title, severity } shape that RiskIndicatorList expects
  const indicators = rawIndicators.map((item, i) => {
    if (typeof item === 'string') {
      const detail = rawDetails[i] ?? {}
      return {
        title:    item,
        severity: detail.severity ?? riskAnalysis.risk_level ?? 'MEDIUM',
        code:     detail.code     ?? null,
        points:   detail.points   ?? null,
        detail:   detail.detail   ?? null,
      }
    }
    return item
  })

  return {
    score:      riskAnalysis.risk_score  ?? null,
    level:      riskAnalysis.risk_level  ?? null,
    indicators,
    breakdown:  rawDetails,
    summary:    null, // backend does not produce a one-line summary yet
  }
}

// ─── VASP adapter ─────────────────────────────────────────────────────────────

/**
 * Build the vasp and path fields from:
 *   - VASP matcher result (exact address match)
 *   - Backend candidate_paths (for displaying the path leading to the VASP)
 */
function adaptVasp(vaspMatch, candidatePaths) {
  if (!vaspMatch || !vaspMatch.found) {
    // No exact match — return the "none" sentinel that VaspAlert.jsx expects
    return {
      vasp: { identified: false },
      path: [],
    }
  }

  // Build path from candidate_paths: find the path whose terminal wallet is the
  // matched VASP address, or fall back to any path ending at that address.
  let matchedPath = null
  const vaspAddrNorm = vaspMatch.address.toLowerCase()

  if (Array.isArray(candidatePaths) && candidatePaths.length > 0) {
    // Prefer shortest path that terminates at or passes through the VASP address
    const sorted = [...candidatePaths].sort((a, b) => (a.hops ?? 99) - (b.hops ?? 99))
    matchedPath =
      sorted.find((p) => (p.terminal_wallet ?? '').toLowerCase() === vaspAddrNorm) ||
      sorted.find((p) => (p.path ?? []).map((a) => a.toLowerCase()).includes(vaspAddrNorm))
  }

  // Convert raw path array of addresses → [{ address, label }] shape for VaspAlert
  const pathNodes = matchedPath
    ? (matchedPath.path ?? []).map((addr) => ({
        address: addr,
        label:   addr.toLowerCase() === vaspAddrNorm ? vaspMatch.name : addr,
      }))
    : []

  return {
    vasp: {
      identified:       true,
      name:             vaspMatch.name,
      type:             vaspMatch.type,
      address:          vaspMatch.address,
      addressType:      vaspMatch.addressType,
      matchType:        vaspMatch.matchType,
      confidence:       vaspMatch.confidencePercent, // percent for existing Meter component
      confidenceScore:  vaspMatch.confidenceScore,
      status:           vaspMatch.status,
      source:           vaspMatch.source,
      sourceUrl:        vaspMatch.sourceUrl,
      hop:              vaspMatch.hop,
      notes:            vaspMatch.notes,
    },
    path: pathNodes,
  }
}

// ─── Main backend response adapter ───────────────────────────────────────────

/**
 * Adapt the full backend CombinedAnalysisResponse → investigation object
 * consumed by the existing Dashboard + component tree.
 *
 * @param {object} raw       - Parsed JSON from /wallet/{address}/analyze
 * @param {string} queried   - The address the user typed (preserved for display)
 * @returns {object}
 */
function adaptBackendResponse(raw, queried) {
  const caseInfo  = raw.case    ?? {}
  const summary   = raw.summary ?? {}
  const risk      = adaptRisk(raw.risk_analysis)

  // Map each transaction
  const transactions = (raw.transactions ?? []).map(adaptTransaction)

  // Use backend's native VASP attribution dataset match
  const backendVasp = raw.vasp_attribution || {};
  
  // Convert backend vasp_attribution shape to the vaspMatch shape expected by adaptVasp
  const vaspMatch = backendVasp.identified ? {
    found: true,
    name: backendVasp.name,
    type: backendVasp.type,
    address: backendVasp.matched_address,
    addressType: backendVasp.address_type || 'exchange_wallet',
    matchType: backendVasp.match_type,
    confidencePercent: backendVasp.confidence_score ? Math.round(backendVasp.confidence_score * 100) : null,
    confidenceScore: backendVasp.confidence_score,
    status: backendVasp.status,
    source: backendVasp.source_name,
    sourceUrl: backendVasp.evidence,
    hop: backendVasp.hop,
    notes: backendVasp.notes
  } : { found: false };

  const { vasp, path } = adaptVasp(vaspMatch, raw.candidate_paths ?? [])

  // Compute a rough total value for the SummaryCards component
  // (sum ETH transfers only; flag as estimated)
  const ethTxs       = (raw.transactions ?? []).filter((t) => (t.asset ?? 'ETH') === 'ETH')
  const totalEthWei  = ethTxs.reduce((acc, t) => acc + (Number(t.value) || 0), 0)
  const totalEth     = Number(totalEthWei.toFixed(4))

  return {
    // ── identity ──────────────────────────────────────────────────────────
    id:             `CT-LIVE-${String(queried).slice(2, 8).toUpperCase()}`,
    suspectWallet:  caseInfo.root_wallet  ?? queried,
    queriedAddress: queried,
    chain:          caseInfo.blockchain   ?? 'ethereum',
    network:        caseInfo.network      ?? 'mainnet',
    isDemo:         false,

    // ── summary metrics ───────────────────────────────────────────────────
    transactionsCount:   summary.transactions_analyzed ?? transactions.length,
    walletsDiscovered:   summary.wallets_discovered    ?? null,
    hops:                summary.max_hop               ?? null,

    // ── transactions ──────────────────────────────────────────────────────
    transactions,

    // ── graph (raw backend payload — consumed by graphUtils adapter) ──────
    _backendGraph: raw.graph ?? null,

    // ── risk ──────────────────────────────────────────────────────────────
    riskScore:      risk?.score      ?? null,
    riskLevel:      risk?.level      ?? null,
    riskIndicators: (risk?.indicators ?? []).map((i) => i.title ?? i),
    risk,                    // full nested object for getInvestigationRisk()

    // ── VASP ──────────────────────────────────────────────────────────────
    vasp,
    path,

    // ── totals (used by SummaryCards) ─────────────────────────────────────
    totalValue:      totalEth,
    totalValueToken: 'ETH',

    // ── entity metadata (future: populated by backend known_entities) ─────
    entityMeta: {},

    // ── disclaimer (from backend) ─────────────────────────────────────────
    disclaimer: raw.disclaimer ?? (
      'INVESTIGATION NOTICE: Analyzed paths represent transaction relationship ' +
      'candidate flows and risk indicators based on observable ledger transfers. ' +
      'They do not constitute conclusive forensic proof of specific fund commingling ' +
      'or legal criminal guilt.'
    ),
  }
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Trace a wallet address.
 *
 * - If the address matches a demo wallet → returns the corresponding mock
 *   investigation instantly (no backend call). This preserves the
 *   "Try Demo Investigation" feature.
 * - Otherwise → calls the real FastAPI backend and adapts the response.
 *
 * @param {string} address
 * @returns {Promise<object>} investigation result
 */
export async function traceWallet(address) {
  const trimmed = typeof address === 'string' ? address.trim() : ''

  if (!trimmed) {
    throw new Error('Please enter a wallet address.')
  }

  const normalized = normalizeAddress(trimmed)

  // ── Demo wallet shortcuts (mock data, no backend call) ────────────────
  if (normalized === normalizeAddress(NO_VASP_DEMO_WALLET)) {
    return { ...noVaspInvestigation, queriedAddress: trimmed }
  }
  if (normalized === normalizeAddress(POSSIBLE_VASP_DEMO_WALLET)) {
    return { ...possibleVaspInvestigation, queriedAddress: trimmed }
  }
  if (normalized === normalizeAddress(DEMO_WALLET)) {
    return {
      ...demoInvestigation,
      queriedAddress: trimmed,
    }
  }

  // ── Real backend call ─────────────────────────────────────────────────
  if (!API_BASE) {
    throw new Error(
      'VITE_API_BASE_URL is not set. ' +
      'Add VITE_API_BASE_URL=http://localhost:8000 to frontend/.env and restart Vite.'
    )
  }

  const url = `${API_BASE}/wallet/${encodeURIComponent(trimmed)}/analyze`

  let response
  try {
    response = await fetch(url, {
      method:  'GET',
      headers: { Accept: 'application/json' },
    })
  } catch (networkErr) {
    // Network-level failure (CORS pre-flight blocked, backend offline, etc.)
    throw new Error(
      `Cannot reach backend at ${API_BASE}. ` +
      `Check that FastAPI is running and CORS allows http://localhost:5173. ` +
      `Network error: ${networkErr.message}`
    )
  }

  if (!response.ok) {
    // Attempt to extract FastAPI error detail for a clear error message
    let detail = `HTTP ${response.status} ${response.statusText}`
    try {
      const errBody = await response.json()
      if (errBody?.detail?.message) detail = errBody.detail.message
      else if (typeof errBody?.detail === 'string') detail = errBody.detail
      else if (errBody?.message) detail = errBody.message
    } catch (_) {
      // ignore parse error — keep the status-based message
    }
    throw new Error(`Backend error: ${detail}`)
  }

  let raw
  try {
    raw = await response.json()
  } catch (parseErr) {
    throw new Error(`Backend returned non-JSON response: ${parseErr.message}`)
  }

  return adaptBackendResponse(raw, trimmed)
}

// Re-export demo wallet constants so Dashboard.jsx keeps its existing import
export { DEMO_WALLET, NO_VASP_DEMO_WALLET, POSSIBLE_VASP_DEMO_WALLET }
