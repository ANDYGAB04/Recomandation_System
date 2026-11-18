const priceFormat = new Intl.NumberFormat('ro-RO', { style: 'currency', currency: 'RON' })


export function formatPrice(value) {
  return priceFormat.format(value)
}

const dateTimeFormat = new Intl.DateTimeFormat('ro-RO', { dateStyle: 'medium', timeStyle: 'short' })


export function formatDateTime(value) {
  return dateTimeFormat.format(new Date(value))
}
