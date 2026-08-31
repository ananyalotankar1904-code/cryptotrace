/**
 * VASP Intelligence Matcher
 *
 * Performs exact, case-insensitive address matching against the local
 * VASP intelligence dataset (vaspdataset/vasp_intelligence_addresses.json).
 *
 * Rules applied (per attribution_rules.json R01):
 *   - Match type : Exact verified address
 *   - Condition  : Destination address exactly matches a known_verified address
 *                  on the same blockchain (ethereum).
 *   - Result     : Return VASP name, entity_type, confidence, and source evidence.
 *
 * For MVP: EXACT VERIFIED ADDRESS MATCHING ONLY.
 * No heuristic, no cluster, no behavioural inference.
 *
 * Do NOT modify this dataset — it mirrors vaspdataset/vasp_intelligence_addresses.json.
 */

// ─── Embedded dataset (mirrors vaspdataset/vasp_intelligence_addresses.json v1.1.0) ───
// Last verified: 2026-08-31
// 7 records — all ethereum / known_verified / confidence high (0.90)
const VASP_RECORDS = [
  {
    record_id: 'eth-binance-14',
    address: '0x28c6c06298d514db089934071355e5743bf21d60',
    entity: 'Binance',
    entity_type: 'VASP',
    blockchain: 'ethereum',
    address_type: 'exchange_wallet',
    attribution_status: 'known_verified',
    confidence: 'high',
    confidence_score: 0.90,
    source_name: 'Etherscan',
    source_url: 'https://etherscan.io/address/0x28c6c06298d514db089934071355e5743bf21d60',
    last_verified_date: '2026-08-31',
    notes: 'Etherscan labels it Binance 14 and Binance / Exchange; this identifies the service, not a customer.',
  },
  {
    record_id: 'eth-binance-deposit-e678',
    address: '0xe67821b76985007b4cf744b0f045c8933b3e91d9',
    entity: 'Binance',
    entity_type: 'VASP',
    blockchain: 'ethereum',
    address_type: 'deposit_address',
    attribution_status: 'known_verified',
    confidence: 'high',
    confidence_score: 0.90,
    source_name: 'Etherscan',
    source_url: 'https://etherscan.io/address/0xe67821b76985007b4cf744b0f045c8933b3e91d9',
    last_verified_date: '2026-08-31',
    notes: 'Etherscan labels it Binance Deposit; this is a deposit endpoint, not a customer identity.',
  },
  {
    record_id: 'eth-coinbase-12',
    address: '0x503828976d22510aad0201ac7ec88293211d23da',
    entity: 'Coinbase',
    entity_type: 'VASP',
    blockchain: 'ethereum',
    address_type: 'exchange_wallet',
    attribution_status: 'known_verified',
    confidence: 'high',
    confidence_score: 0.90,
    source_name: 'Etherscan',
    source_url: 'https://etherscan.io/address/0x503828976d22510aad0201ac7ec88293211d23da',
    last_verified_date: '2026-08-31',
    notes: 'Etherscan labels it Coinbase 12 and Coinbase / Exchange (also Fiat Gateway).',
  },
  {
    record_id: 'eth-kucoin-1',
    address: '0x2b5634c42055806a59e9107ed44d43c426e58258',
    entity: 'KuCoin',
    entity_type: 'VASP',
    blockchain: 'ethereum',
    address_type: 'exchange_wallet',
    attribution_status: 'known_verified',
    confidence: 'high',
    confidence_score: 0.90,
    source_name: 'Etherscan',
    source_url: 'https://etherscan.io/address/0x2b5634c42055806a59e9107ed44d43c426e58258',
    last_verified_date: '2026-08-31',
    notes: 'Etherscan labels it KuCoin 1 and KuCoin / Exchange.',
  },
  {
    record_id: 'eth-htx-1',
    address: '0xab5c66752a9e8167967685f1450532fb96d5d24f',
    entity: 'HTX',
    entity_type: 'VASP',
    blockchain: 'ethereum',
    address_type: 'exchange_wallet',
    attribution_status: 'known_verified',
    confidence: 'high',
    confidence_score: 0.90,
    source_name: 'Etherscan',
    source_url: 'https://etherscan.io/address/0xab5c66752a9e8167967685f1450532fb96d5d24f',
    last_verified_date: '2026-08-31',
    notes: 'Etherscan labels it HTX 1; HTX is the current name of Huobi.',
  },
  {
    record_id: 'eth-bitfinex-3',
    address: '0x876eabf441b2ee5b5b0554fd502a8e0600950cfa',
    entity: 'Bitfinex',
    entity_type: 'VASP',
    blockchain: 'ethereum',
    address_type: 'exchange_wallet',
    attribution_status: 'known_verified',
    confidence: 'high',
    confidence_score: 0.90,
    source_name: 'Etherscan',
    source_url: 'https://etherscan.io/address/0x876eabf441b2ee5b5b0554fd502a8e0600950cfa',
    last_verified_date: '2026-08-31',
    notes: 'Etherscan labels it Bitfinex 3 and Bitfinex / Exchange.',
  },
  {
    record_id: 'eth-gate-deposit-0d07',
    address: '0x0d0707963952f2fba59dd06f2b425ace40b492fe',
    entity: 'Gate.io',
    entity_type: 'VASP',
    blockchain: 'ethereum',
    address_type: 'deposit_address',
    attribution_status: 'known_verified',
    confidence: 'high',
    confidence_score: 0.90,
    source_name: 'Etherscan',
    source_url: 'https://etherscan.io/address/0x0d0707963952f2fba59dd06f2b425ace40b492fe',
    last_verified_date: '2026-08-31',
    notes: 'Etherscan labels it Gate Deposit; this is a deposit endpoint, not a customer identity.',
  },
]

// Pre-build a normalised lookup for O(1) address matching.
// Key: lowercase address. Value: dataset record.
const VASP_LOOKUP = Object.fromEntries(
  VASP_RECORDS
    .filter((r) => r.attribution_status === 'known_verified')
    .map((r) => [r.address.toLowerCase(), r])
)

/**
 * Look up a single address against the VASP dataset.
 *
 * @param {string} address  - Ethereum address (any case)
 * @param {string} blockchain - Expected blockchain (default "ethereum")
 * @returns {object|null}   - Matched VASP record or null
 */
function lookupAddress(address, blockchain = 'ethereum') {
  if (!address || typeof address !== 'string') return null
  const norm = address.trim().toLowerCase()
  const record = VASP_LOOKUP[norm]
  if (!record) return null
  // Only match if the record belongs to the same blockchain
  if (record.blockchain.toLowerCase() !== blockchain.toLowerCase()) return null
  return record
}

/**
 * Search a list of destination addresses for the earliest exact VASP match.
 *
 * The array should be ordered by hop (ascending) so the nearest match is returned.
 * For the MVP this implements Rule R01 only: exact verified address matching.
 *
 * @param {Array<{address: string, hop: number|null}>} destinations
 *   - Objects with at least { address, hop }.
 *   - OR plain strings (address only; hop treated as null).
 * @param {string} blockchain  - "ethereum" etc.
 * @returns {{
 *   found: boolean,
 *   name: string|null,
 *   type: string|null,
 *   address: string|null,
 *   addressType: string|null,
 *   matchType: string,
 *   confidence: string|null,
 *   confidenceScore: number|null,
 *   confidencePercent: number|null,
 *   source: string|null,
 *   sourceUrl: string|null,
 *   hop: number|null,
 *   identified: boolean,
 *   status: string,
 *   notes: string|null,
 * }}
 */
export function findVaspMatch(destinations, blockchain = 'ethereum') {
  const NO_MATCH = {
    found: false,
    name: null,
    type: null,
    address: null,
    addressType: null,
    matchType: 'No match',
    confidence: null,
    confidenceScore: null,
    confidencePercent: null,
    source: null,
    sourceUrl: null,
    hop: null,
    identified: false,
    status: 'No verified dataset match',
    notes: null,
  }

  if (!destinations || destinations.length === 0) return NO_MATCH

  for (const dest of destinations) {
    const addr = typeof dest === 'string' ? dest : dest.address
    const hop  = typeof dest === 'string' ? null : (dest.hop ?? null)
    const record = lookupAddress(addr, blockchain)
    if (record) {
      const pct = Math.round(record.confidence_score * 100)
      return {
        found: true,
        name: record.entity,
        type: record.entity_type,
        address: record.address,
        addressType: record.address_type,
        matchType: 'Exact verified address',
        confidence: record.confidence,
        confidenceScore: record.confidence_score,
        confidencePercent: pct,
        source: record.source_name,
        sourceUrl: record.source_url,
        hop,
        identified: true,
        status: `known_verified · ${record.source_name}`,
        notes: record.notes,
      }
    }
  }

  return NO_MATCH
}

/**
 * Convenience: given the raw backend transaction array, collect all unique
 * destination addresses ordered by hop (ascending) and run VASP matching.
 *
 * @param {Array<object>} transactions  - Raw backend transaction records (snake_case)
 * @param {string} blockchain
 * @returns {object} - Result from findVaspMatch()
 */
export function matchVaspFromTransactions(transactions, blockchain = 'ethereum') {
  if (!Array.isArray(transactions) || transactions.length === 0) {
    return findVaspMatch([], blockchain)
  }

  // Collect unique destinations ordered by hop ascending (nearest first)
  const seen = new Set()
  const destinations = []

  const sorted = [...transactions].sort((a, b) => (a.hop ?? 99) - (b.hop ?? 99))
  for (const tx of sorted) {
    const addr = (tx.to_address || tx.to || '').toLowerCase()
    if (addr && !seen.has(addr)) {
      seen.add(addr)
      destinations.push({ address: addr, hop: tx.hop ?? null })
    }
  }

  return findVaspMatch(destinations, blockchain)
}
