const MONTHS = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

/**
 * Formats mock timestamps such as "2026-08-20 10:30".
 * Returns null if the value is missing.
 */
export function formatTimestamp(value) {
  if (!value) {
    return null
  }

  const match = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/.exec(String(value))
  if (!match) {
    return { date: String(value), time: null }
  }

  const hour = Number(match[4])
  const hour12 = hour % 12 || 12
  const suffix = hour >= 12 ? 'PM' : 'AM'

  return {
    date: `${Number(match[3])} ${MONTHS[Number(match[2]) - 1]} ${match[1]}`,
    time: `${hour12}:${match[5]} ${suffix}`,
  }
}
