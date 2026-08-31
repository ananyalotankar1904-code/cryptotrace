/**
 * Shortens a wallet address for display.
 * Example: 0x71C123...A92
 */
export function formatAddress(address, start = 5, end = 3) {
  if (!address) {
    return '—'
  }

  if (address.length <= start + end + 3) {
    return address
  }

  return `${address.slice(0, start)}...${address.slice(-end)}`
}
