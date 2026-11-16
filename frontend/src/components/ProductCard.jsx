import { Link, useLocation } from 'react-router-dom'
import { formatPrice } from '../lib/format.js'
import { useVocabulary } from '../lib/vocabulary.js'
import { AvailabilityBadge } from './Status.jsx'

const MAX_TAGS = 3

/**
 * Cardul unui produs în grilă; tot cardul e clicabil.
 * `children` apare sub preț (de exemplu, explicația unei recomandări); elementele interactive
 * din `children` au nevoie de `relative z-10`, ca să fie deasupra linkului.
 */
export default function ProductCard({ product, children }) {
  const { label } = useVocabulary()
  const location = useLocation()
  const tags = [...product.styles.map((s) => label('styles', s)), ...product.tags]

  return (
    <article
      className={`relative flex h-full flex-col rounded-xl border bg-white p-4 shadow-sm transition hover:shadow-md ${
        product.available ? 'border-gray-200' : 'border-gray-200 opacity-75'
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-800">
          {label('activities', product.category)}
        </span>
        <AvailabilityBadge available={product.available} />
      </div>

      <h2 className="mt-3 text-base font-semibold leading-snug text-gray-900">
        {/* Linkul acoperă tot cardul; păstrăm filtrele catalogului pentru butonul „Înapoi”. */}
        <Link
          to={`/produs/${product.id}`}
          state={{ from: location }}
          className="after:absolute after:inset-0 hover:text-emerald-800 focus:outline-none"
        >
          {product.name}
        </Link>
      </h2>

      <ul className="mt-2 flex flex-wrap gap-1" aria-label="Etichete">
        {tags.slice(0, MAX_TAGS).map((tag, i) => (
          <li key={`${i}-${tag}`} className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
            {tag}
          </li>
        ))}
        {tags.length > MAX_TAGS && <li className="px-1 text-xs text-gray-400">+{tags.length - MAX_TAGS}</li>}
      </ul>

      <p className="mt-auto pt-4 text-lg font-semibold text-gray-900">{formatPrice(product.price)}</p>
      {children}
    </article>
  )
}
