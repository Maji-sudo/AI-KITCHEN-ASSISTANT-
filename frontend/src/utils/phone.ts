/**
 * Phone number validation and normalization utilities for tel: URI dialler actions.
 */

/**
 * Normalizes and validates a phone number string for use in tel: URLs.
 * - Trims whitespace
 * - Rejects null, empty, or placeholder strings (e.g. 'n/a', 'none', 'unavailable')
 * - Preserves leading '+' for international numbers
 * - Strips non-digit formatting characters (parentheses, hyphens, spaces, periods)
 * - Verifies digit count is within standard telephony bounds (6 to 15 digits)
 *
 * @returns Normalized phone string suitable for tel: URI, or null if invalid.
 */
export function normalizePhoneNumber(phone?: string | null): string | null {
  if (!phone || typeof phone !== 'string') {
    return null
  }

  const trimmed = phone.trim()
  if (!trimmed) {
    return null
  }

  const lower = trimmed.toLowerCase()
  if (['n/a', 'none', 'null', 'undefined', 'not available', 'unavailable', 'no phone'].includes(lower)) {
    return null
  }

  // Preserve leading '+' if present
  const hasLeadingPlus = trimmed.startsWith('+')
  const digitsOnly = trimmed.replace(/\D/g, '')

  // Telephony standards: between 6 and 15 digits (ITU-T E.164 max length)
  if (digitsOnly.length < 6 || digitsOnly.length > 15) {
    return null
  }

  return hasLeadingPlus ? `+${digitsOnly}` : digitsOnly
}

/**
 * Checks whether a given phone number string is valid for dialing.
 */
export function isValidPhoneNumber(phone?: string | null): boolean {
  return normalizePhoneNumber(phone) !== null
}

/**
 * Formats a phone number for dialler execution via tel: URI.
 * Throws an Error if the phone number is invalid.
 */
export function createTelUri(phone?: string | null): string {
  const normalized = normalizePhoneNumber(phone)
  if (!normalized) {
    throw new Error('Phone number unavailable or invalid.')
  }
  return `tel:${encodeURIComponent(normalized)}`
}
