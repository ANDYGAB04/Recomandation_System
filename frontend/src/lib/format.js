const priceFormat = new Intl.NumberFormat('ro-RO', { style: 'currency', currency: 'RON' })

/** 899.99 → "899,99 RON" */
export function formatPrice(value) {
  return priceFormat.format(value)
}

const dateTimeFormat = new Intl.DateTimeFormat('ro-RO', { dateStyle: 'medium', timeStyle: 'short' })

/** "2026-11-15T14:30:00Z" → "15 nov. 2026, 16:30" (ora locală) */
export function formatDateTime(value) {
  return dateTimeFormat.format(new Date(value))
}
