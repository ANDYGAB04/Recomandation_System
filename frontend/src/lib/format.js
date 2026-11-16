const priceFormat = new Intl.NumberFormat('ro-RO', { style: 'currency', currency: 'RON' })

/** 899.99 → "899,99 RON" */
export function formatPrice(value) {
  return priceFormat.format(value)
}
