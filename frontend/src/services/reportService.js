/**
 * Report Service — Phase 9
 *
 * Handles communication with the backend PDF report generation endpoint.
 *
 * NOTE: The frontend MUST NOT generate or format the PDF itself.
 * The backend is solely responsible for creating, formatting, and returning the PDF file.
 *
 * BACKEND INTEGRATION POINT:
 * - Configure the base URL via the `VITE_API_BASE_URL` environment variable.
 * - Replace `REPORT_ENDPOINT_PATH` below if your backend uses a different endpoint path.
 * - If your backend expects a different payload schema, adjust `buildReportPayload()`.
 */

// Configurable API base URL (e.g. VITE_API_BASE_URL=http://localhost:8000)
const API_BASE_URL = (
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) ||
  ''
).replace(/\/+$/, '')

// Backend endpoint path for PDF report generation
export const REPORT_ENDPOINT_PATH = '/api/reports/investigation'

/**
 * Returns the full URL to the backend report generation endpoint.
 */
export function getReportEndpointUrl() {
  return `${API_BASE_URL}${REPORT_ENDPOINT_PATH}`
}

/**
 * Sanitizes an identifier for safe use in a filename.
 * @param {string} id
 * @returns {string}
 */
function sanitizeFilenameId(id) {
  if (!id || typeof id !== 'string') return ''
  // Remove non-alphanumeric, dashes, underscores, and trim
  return id.replace(/[^a-zA-Z0-9_-]/g, '').trim()
}

/**
 * Generates a standard professional filename for the downloaded report.
 * Avoids long wallet hashes in filenames.
 *
 * @param {string|null|undefined} investigationId
 * @returns {string} e.g. "CryptoTrace_Investigation_Report_CT-2026-8941.pdf"
 */
export function generateReportFilename(investigationId) {
  const safeId = sanitizeFilenameId(investigationId)
  if (safeId) {
    return `CryptoTrace_Investigation_Report_${safeId}.pdf`
  }
  return 'CryptoTrace_Investigation_Report.pdf'
}

/**
 * Initiates a browser download for a received binary Blob.
 *
 * @param {Blob} blob - Binary PDF data received from the backend
 * @param {string} filename - Target download filename
 */
export function downloadBlob(blob, filename) {
  if (!(blob instanceof Blob)) {
    throw new Error('Invalid file data received.')
  }

  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'

  document.body.appendChild(link)
  link.click()

  // Clean up object URL and temporary DOM node
  setTimeout(() => {
    if (document.body.contains(link)) {
      document.body.removeChild(link)
    }
    window.URL.revokeObjectURL(url)
  }, 200)
}

/**
 * Extracts and structures the complete current investigation data
 * to send to the backend PDF generator.
 *
 * @param {object} investigation - Current React investigation state
 * @returns {object} Formatted payload matching backend expectations
 */
export function buildReportPayload(investigation) {
  if (!investigation) {
    throw new Error('No active investigation data to export.')
  }

  const investigationId =
    investigation.id ||
    investigation.investigationId ||
    `INV-${(investigation.suspectWallet || 'UNKNOWN').slice(2, 8).toUpperCase()}`

  // Complete transactions list (complete investigation dataset, not filtered view)
  const transactions = (investigation.transactions || []).map((tx) => ({
    id: tx.id,
    from: tx.from,
    to: tx.to,
    amount: tx.amount,
    token: tx.token,
    timestamp: tx.timestamp,
    hop: tx.hop,
    risk: tx.risk,
    status: tx.status,
    txHash: tx.txHash,
    block: tx.block,
  }))

  const suspectMeta = investigation.entityMeta?.[investigation.suspectWallet] || {}
  const rawIndicators =
    investigation.risk?.indicators ||
    investigation.riskIndicators ||
    suspectMeta.indicators ||
    []

  // Complete risk structure
  const risk = {
    score: investigation.risk?.score ?? investigation.riskScore ?? null,
    level: investigation.risk?.level ?? investigation.riskLevel ?? null,
    summary: investigation.risk?.summary || '',
    indicators: rawIndicators.map((item) =>
      typeof item === 'string'
        ? { title: item, severity: investigation.risk?.level || investigation.riskLevel || 'MEDIUM', description: '' }
        : { title: item.title, severity: item.severity || 'MEDIUM', description: item.description || '' }
    ),
    breakdown: investigation.risk?.breakdown || [],
  }

  // Complete VASP structure
  const vasp = investigation.vasp
    ? {
        identified: Boolean(investigation.vasp.identified),
        possible: Boolean(investigation.vasp.possible),
        name: investigation.vasp.name || 'Unknown',
        type: investigation.vasp.type || 'Exchange / VASP',
        confidence: investigation.vasp.confidence ?? null,
        address: investigation.vasp.address || null,
        hop: investigation.vasp.hop ?? null,
        finalDestinationHop: investigation.vasp.finalDestinationHop ?? null,
        status: investigation.vasp.status || '',
      }
    : null

  // Complete fund flow path
  const path = (investigation.path || []).map((node) => ({
    label: node.label,
    address: node.address,
  }))

  return {
    investigationId,
    suspectWallet: investigation.suspectWallet,
    queriedAddress: investigation.queriedAddress || investigation.suspectWallet,
    chain: investigation.chain || 'Ethereum',
    hops: investigation.hops ?? 0,
    totalValue: investigation.totalValue ?? null,
    totalValueToken: investigation.totalValueToken || 'ETH',
    transactionsCount: investigation.transactionsCount || transactions.length,
    risk,
    vasp,
    path,
    transactions,
    entityMeta: investigation.entityMeta || {},
    isDemo: Boolean(investigation.isDemo),
    generatedAt: new Date().toISOString(),
  }
}

/**
 * Sends the current investigation data to the backend PDF generator endpoint,
 * receives the generated PDF binary blob, and triggers browser download.
 *
 * @param {object} investigation - Current React investigation state
 * @returns {Promise<{ success: boolean, filename: string }>}
 */
export async function generateInvestigationReport(investigation) {
  if (!investigation) {
    throw new Error('Please load an investigation before generating a report.')
  }

  const payload = buildReportPayload(investigation)
  const endpointUrl = getReportEndpointUrl()

  let response
  try {
    response = await fetch(endpointUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/pdf, application/json',
      },
      body: JSON.stringify(payload),
    })
  } catch (err) {
    // Network / offline error (backend server not running or connection refused)
    if (err instanceof TypeError && /fetch|network|failed/i.test(err.message)) {
      throw new Error('Report service is currently unavailable.')
    }
    throw new Error('Report service is currently unavailable.')
  }

  if (!response.ok) {
    let serverMessage = ''
    try {
      const errorJson = await response.json()
      serverMessage = errorJson.message || errorJson.error || ''
    } catch {
      // Non-JSON error response from backend
    }

    if (
      response.status === 404 ||
      response.status === 502 ||
      response.status === 503 ||
      response.status === 504
    ) {
      throw new Error('Report service is currently unavailable.')
    }

    throw new Error(
      serverMessage || 'Unable to generate the investigation report. Please try again.'
    )
  }

  // Handle binary PDF blob
  let blob
  try {
    blob = await response.blob()
  } catch {
    throw new Error('Unable to generate the investigation report. Please try again.')
  }

  if (!blob || blob.size === 0) {
    throw new Error('Unable to generate the investigation report. Please try again.')
  }

  const filename = generateReportFilename(payload.investigationId)
  downloadBlob(blob, filename)

  return {
    success: true,
    filename,
  }
}
