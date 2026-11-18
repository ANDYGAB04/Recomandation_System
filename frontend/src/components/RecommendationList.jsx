import { Link } from 'react-router-dom'
import FeedbackButtons from './FeedbackButtons.jsx'
import ProductCard from './ProductCard.jsx'
import { EmptyState, ErrorState } from './Status.jsx'
import { errorMessage } from '../lib/api.js'


export function RecommendationCard({ item, scoreLabel, strategy }) {
  const { product, score, explanation } = item
  return (
    <ProductCard product={product}>
      <div className="mt-3 border-t border-gray-100 pt-3">
        {scoreLabel && (
          <p className="text-xs font-semibold text-emerald-800">
            {scoreLabel} {Math.round(score * 100)}%
          </p>
        )}
        <p className="mt-1 text-sm leading-snug text-gray-600">{explanation.text}</p>
      </div>
      {strategy && <FeedbackButtons productId={product.id} strategy={strategy} />}
    </ProductCard>
  )
}


export function FallbackNotice({ reason }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      <p>
        <span className="font-semibold">Îți arătăm cele mai cumpărate produse.</span> {reason}
      </p>
      <Link
        to="/setari"
        className="rounded-md bg-white px-3 py-1.5 font-medium text-amber-900 shadow-sm ring-1 ring-amber-200 hover:bg-amber-100"
      >
        Mergi la setări
      </Link>
    </div>
  )
}


export default function RecommendationList({
  resource,
  scoreLabel = 'Potrivire',
  columns = 4,
  skeletonCount = 4,
  emptyState,
  withFeedback = false,
}) {
  const { status, data, error, reload } = resource
  const grid = `grid gap-4 sm:grid-cols-2 ${columns >= 3 ? 'lg:grid-cols-3' : ''} ${columns >= 4 ? 'xl:grid-cols-4' : ''}`

  if (status === 'error') {
    const unavailable = error?.status === 503
    return (
      <ErrorState
        title={unavailable ? 'Recomandările nu sunt disponibile încă.' : 'Nu am putut încărca recomandările.'}
        message={errorMessage(error)}
        onRetry={reload}
      />
    )
  }
  if (!data) {
    return (
      <ul className={grid} aria-busy="true" aria-label="Se încarcă recomandările">
        {Array.from({ length: skeletonCount }, (_, i) => (
          <li key={i} className="h-60 animate-pulse rounded-xl border border-gray-200 bg-white p-4">
            <div className="h-4 w-20 rounded bg-gray-200" />
            <div className="mt-4 h-4 w-3/4 rounded bg-gray-200" />
            <div className="mt-2 h-3 w-1/2 rounded bg-gray-100" />
            <div className="mt-10 h-5 w-24 rounded bg-gray-200" />
            <div className="mt-4 h-3 w-full rounded bg-gray-100" />
            <div className="mt-2 h-3 w-2/3 rounded bg-gray-100" />
          </li>
        ))}
      </ul>
    )
  }

  const popular = data.strategy === 'popular'
  return (
    <div className="space-y-4">
      {}
      {popular && data.items.length > 0 && <FallbackNotice reason={data.fallback_reason} />}
      {data.items.length === 0 ? (
        emptyState ?? <EmptyState title="Nu am găsit produse potrivite." />
      ) : (
        <ul className={`${grid} ${status === 'loading' ? 'opacity-60 transition-opacity' : ''}`} aria-busy={status === 'loading'}>
          {data.items.map((item) => (
            <li key={item.product.id}>
              <RecommendationCard
                item={item}
                scoreLabel={popular ? null : scoreLabel}
                strategy={withFeedback ? data.strategy : undefined}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
