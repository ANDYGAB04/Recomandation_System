import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import ProductCard from '../components/ProductCard.jsx'
import Spinner from '../components/Spinner.jsx'
import { EmptyState, ErrorState } from '../components/Status.jsx'
import { errorMessage } from '../lib/api.js'
import { formatDateTime, formatPrice } from '../lib/format.js'
import { sendInteraction, useHistory } from '../lib/interactions.js'
import { notifyUserDataChanged } from '../lib/userData.js'
import { useVocabulary } from '../lib/vocabulary.js'

const EVENT_STYLES = {
  view: 'bg-gray-100 text-gray-700',
  favorite: 'bg-amber-100 text-amber-800',
  unfavorite: 'bg-gray-100 text-gray-500',
  purchase: 'bg-emerald-100 text-emerald-800',
}

function Section({ title, count, children }) {
  return (
    <section className="space-y-3">
      <h2 className="flex items-baseline gap-2 text-lg font-semibold text-gray-900">
        {title}
        {count !== undefined && <span className="text-sm font-normal text-gray-500">({count})</span>}
      </h2>
      {children}
    </section>
  )
}

export default function HistoryPage() {
  const history = useHistory()
  const { label } = useVocabulary()

  if (history.status === 'error') {
    return <ErrorState title="Nu am putut încărca istoricul." message={errorMessage(history.error)} onRetry={history.reload} />
  }
  if (!history.data) return <Spinner label="Se încarcă istoricul…" />

  const { favorites, purchases, events } = history.data

  return (
    <div className={`space-y-10 ${history.status === 'loading' ? 'opacity-70 transition-opacity' : ''}`}>
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Favorite și istoric</h1>
        <p className="mt-1 text-sm text-gray-600">
          Ce salvezi, ce cumperi și ce deschizi în aplicație influențează recomandările tale.
        </p>
      </div>

      <Section title="Favorite" count={favorites.length}>
        {favorites.length === 0 ? (
          <EmptyState
            title="Nu ai încă produse favorite."
            message="Deschide un produs din catalog și apasă „Adaugă la favorite”."
            action={<CatalogLink />}
          />
        ) : (
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {favorites.map((product) => (
              <li key={product.id}>
                <ProductCard product={product}>
                  <RemoveFavorite productId={product.id} />
                </ProductCard>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Cumpărături (simulate)" count={purchases.length}>
        {purchases.length === 0 ? (
          <EmptyState title="Nu ai cumpărat încă nimic." message="Cumpărăturile sunt simulate: nu se plătește nimic." />
        ) : (
          <ul className="divide-y divide-gray-100 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
            {purchases.map(({ product, purchased_at }) => (
              <li key={product.id} className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <Link to={`/produs/${product.id}`} className="font-medium text-gray-900 hover:text-emerald-800">
                    {product.name}
                  </Link>
                  <p className="text-xs text-gray-500">{label('activities', product.category)}</p>
                </div>
                <div className="flex items-center gap-4 text-sm sm:text-right">
                  <span className="font-semibold text-gray-900">{formatPrice(product.price)}</span>
                  <time dateTime={purchased_at} className="text-gray-500">
                    {formatDateTime(purchased_at)}
                  </time>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Evenimente recente" count={events.length}>
        {events.length === 0 ? (
          <EmptyState title="Niciun eveniment încă." message="Vizualizările, favoritele și cumpărăturile apar aici." />
        ) : (
          <>
            <ol className="divide-y divide-gray-100 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
              {events.map((event) => (
                <li key={event.event_id} className="flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2.5 text-sm">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${EVENT_STYLES[event.type] ?? EVENT_STYLES.view}`}>
                    {label('event_types', event.type)}
                  </span>
                  <Link to={`/produs/${event.product.id}`} className="min-w-0 flex-1 truncate text-gray-900 hover:text-emerald-800">
                    {event.product.name}
                  </Link>
                  <time dateTime={event.created_at} className="text-xs text-gray-500">
                    {formatDateTime(event.created_at)}
                  </time>
                </li>
              ))}
            </ol>
            <p className="text-xs text-gray-500">Se afișează ultimele 50 de evenimente, cele mai noi primele.</p>
          </>
        )}
      </Section>
    </div>
  )
}

function CatalogLink() {
  return (
    <Link to="/catalog" className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800">
      Mergi la catalog
    </Link>
  )
}


function RemoveFavorite({ productId }) {
  const busy = useRef(false)
  const [state, setState] = useState({ pending: false, error: '' })

  async function remove() {
    if (busy.current) return
    busy.current = true
    setState({ pending: true, error: '' })
    try {
      await sendInteraction(productId, 'unfavorite')
      notifyUserDataChanged() 
    } catch (error) {
      setState({ pending: false, error: errorMessage(error) })
    } finally {
      busy.current = false
    }
  }

  return (
    <div className="relative z-10 mt-3">
      <button
        type="button"
        onClick={remove}
        disabled={state.pending}
        className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:border-red-300 hover:text-red-700 disabled:opacity-60"
      >
        {state.pending ? 'Se scoate…' : 'Scoate din favorite'}
      </button>
      {state.error && <p className="mt-1 text-xs text-red-600">{state.error}</p>}
    </div>
  )
}
