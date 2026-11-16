import { useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import ProductCard from '../components/ProductCard.jsx'
import RecommendedStrip from '../components/RecommendedStrip.jsx'
import { EmptyState, ErrorState, TestDataBadge } from '../components/Status.jsx'
import { api, errorMessage } from '../lib/api.js'
import { useVocabulary } from '../lib/vocabulary.js'

const PAGE_SIZE = 24
const SEARCH_DELAY_MS = 300

/** Filtrele stau în adresa paginii (?categorie=…&q=…), ca să se păstreze la „Înapoi” și la reîncărcare. */
function readFilters(params) {
  const page = Number.parseInt(params.get('pagina') ?? '1', 10)
  return {
    category: params.get('categorie') ?? '',
    q: params.get('q') ?? '',
    maxPrice: params.get('pret_maxim') ?? '',
    availableOnly: params.get('disponibile') === '1',
    page: Number.isFinite(page) && page > 0 ? page : 1,
  }
}

function writeFilters({ category, q, maxPrice, availableOnly, page }) {
  const params = new URLSearchParams()
  if (category) params.set('categorie', category)
  if (q.trim()) params.set('q', q.trim())
  if (maxPrice) params.set('pret_maxim', maxPrice)
  if (availableOnly) params.set('disponibile', '1')
  if (page > 1) params.set('pagina', String(page))
  return params
}

function apiQuery({ category, q, maxPrice, availableOnly, page }) {
  const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String((page - 1) * PAGE_SIZE) })
  if (category) params.set('category', category)
  if (q.trim()) params.set('q', q.trim())
  if (maxPrice && Number(maxPrice) >= 0) params.set('max_price', maxPrice)
  if (availableOnly) params.set('available_only', 'true')
  return params.toString()
}

export default function CatalogPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = readFilters(searchParams)
  const { options } = useVocabulary()

  // Textul căutării se actualizează imediat în câmp, dar în adresă (și la API) după o mică pauză.
  const [searchText, setSearchText] = useState(filters.q)
  const [priceText, setPriceText] = useState(filters.maxPrice)
  const [state, setState] = useState({ status: 'loading', data: null, error: null })
  const [reloadKey, setReloadKey] = useState(0)

  const setFilters = useCallback(
    (changes) => {
      // Orice schimbare de filtru (în afară de pagină) revine la prima pagină.
      const next = { ...readFilters(searchParams), page: 1, ...changes }
      setSearchParams(writeFilters(next), { replace: !('page' in changes) })
    },
    [searchParams, setSearchParams],
  )

  // Ultimele valori scrise de noi în adresă: nu le copiem înapoi în câmpuri, ca să nu pierdem
  // caracterele tastate între timp.
  const pushed = useRef({ q: filters.q, maxPrice: filters.maxPrice })

  // Câmpurile urmăresc adresa când se schimbă din afară (de exemplu, butonul „Înapoi”).
  useEffect(() => {
    if (filters.q !== pushed.current.q) setSearchText(filters.q)
    pushed.current.q = filters.q
  }, [filters.q])
  useEffect(() => {
    if (filters.maxPrice !== pushed.current.maxPrice) setPriceText(filters.maxPrice)
    pushed.current.maxPrice = filters.maxPrice
  }, [filters.maxPrice])

  useEffect(() => {
    if (searchText.trim() === filters.q.trim()) return
    const timer = setTimeout(() => {
      pushed.current.q = searchText.trim()
      setFilters({ q: searchText })
    }, SEARCH_DELAY_MS)
    return () => clearTimeout(timer)
  }, [searchText, filters.q, setFilters])

  useEffect(() => {
    if (priceText === filters.maxPrice) return
    const timer = setTimeout(() => {
      pushed.current.maxPrice = priceText
      setFilters({ maxPrice: priceText })
    }, SEARCH_DELAY_MS)
    return () => clearTimeout(timer)
  }, [priceText, filters.maxPrice, setFilters])

  const query = apiQuery(filters)
  useEffect(() => {
    let active = true
    setState((current) => ({ ...current, status: 'loading', error: null }))
    api
      .get(`/products?${query}`)
      .then((data) => active && setState({ status: 'ready', data, error: null }))
      .catch((error) => active && setState({ status: 'error', data: null, error }))
    return () => {
      active = false
    }
  }, [query, reloadKey])

  const hasFilters = Boolean(filters.category || filters.q || filters.maxPrice || filters.availableOnly)
  const resetFilters = () => {
    setSearchText('')
    setPriceText('')
    setSearchParams(new URLSearchParams(), { replace: true })
  }

  const data = state.data
  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Catalog</h1>
          <p className="mt-1 text-sm text-gray-600">
            Echipament pentru drumeție, camping, alergare și ciclism.{' '}
            <TestDataBadge className="align-middle" />
          </p>
        </div>
        {data && state.status === 'ready' && (
          <p className="text-sm text-gray-500" aria-live="polite">
            {data.total === 1 ? '1 produs' : `${data.total} produse`}
          </p>
        )}
      </div>

      {/* Recomandările apar doar pe prima pagină a catalogului, fără filtre. */}
      {!hasFilters && filters.page === 1 && (
        <div className="mt-6">
          <RecommendedStrip />
        </div>
      )}

      {/* Filtre */}
      <div className="mt-6 space-y-4 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap gap-2" role="group" aria-label="Categorie">
          {[{ value: '', label: 'Toate' }, ...options('activities')].map((option) => {
            const active = filters.category === option.value
            return (
              <button
                key={option.value || 'toate'}
                type="button"
                aria-pressed={active}
                onClick={() => setFilters({ category: option.value })}
                className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
                  active ? 'bg-emerald-700 text-white' : 'bg-gray-100 text-gray-700 hover:bg-emerald-50 hover:text-emerald-800'
                }`}
              >
                {option.label}
              </button>
            )
          })}
        </div>

        <div className="grid gap-3 sm:grid-cols-[1fr_auto_auto] sm:items-end">
          <label className="block">
            <span className="text-sm font-medium text-gray-700">Caută</span>
            <input
              type="search"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              placeholder="de exemplu: cort, impermeabil, merinos"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-200"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-gray-700">Preț maxim (RON)</span>
            <input
              type="number"
              min="0"
              step="10"
              inputMode="numeric"
              value={priceText}
              onChange={(event) => setPriceText(event.target.value)}
              placeholder="fără limită"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-200 sm:w-40"
            />
          </label>
          <label className="flex items-center gap-2 py-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={filters.availableOnly}
              onChange={(event) => setFilters({ availableOnly: event.target.checked })}
              className="h-4 w-4 rounded border-gray-300 accent-emerald-700"
            />
            Doar produse în stoc
          </label>
        </div>

        {hasFilters && (
          <button type="button" onClick={resetFilters} className="text-sm font-medium text-emerald-700 hover:text-emerald-900">
            Resetează filtrele
          </button>
        )}
      </div>

      {/* Rezultate */}
      <div className="mt-6">
        {state.status === 'error' ? (
          <ErrorState message={errorMessage(state.error)} onRetry={() => setReloadKey((key) => key + 1)} />
        ) : state.status === 'loading' && !data ? (
          <ProductGridSkeleton />
        ) : data.items.length === 0 ? (
          <EmptyState
            title="Niciun produs nu se potrivește filtrelor."
            message={hasFilters ? 'Încearcă alte filtre sau resetează-le.' : 'Catalogul este gol. Rulează scriptul de inițializare.'}
            action={
              hasFilters && (
                <button
                  type="button"
                  onClick={resetFilters}
                  className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800"
                >
                  Resetează filtrele
                </button>
              )
            }
          />
        ) : (
          <>
            <ul
              className={`grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 ${
                state.status === 'loading' ? 'opacity-60 transition-opacity' : ''
              }`}
              aria-busy={state.status === 'loading'}
            >
              {data.items.map((product) => (
                <li key={product.id}>
                  <ProductCard product={product} />
                </li>
              ))}
            </ul>
            {totalPages > 1 && (
              <Pagination page={filters.page} totalPages={totalPages} onChange={(page) => setFilters({ page })} />
            )}
          </>
        )}
      </div>
    </section>
  )
}

function Pagination({ page, totalPages, onChange }) {
  const go = (target) => {
    onChange(target)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  const buttonClass =
    'rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:border-emerald-600 hover:text-emerald-800 disabled:cursor-not-allowed disabled:opacity-40'
  return (
    <nav className="mt-8 flex items-center justify-center gap-3" aria-label="Paginare">
      <button type="button" className={buttonClass} disabled={page <= 1} onClick={() => go(page - 1)}>
        ← Înapoi
      </button>
      <span className="text-sm text-gray-600">
        Pagina {Math.min(page, totalPages)} din {totalPages}
      </span>
      <button type="button" className={buttonClass} disabled={page >= totalPages} onClick={() => go(page + 1)}>
        Înainte →
      </button>
    </nav>
  )
}

function ProductGridSkeleton() {
  return (
    <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" aria-busy="true" aria-label="Se încarcă produsele">
      {Array.from({ length: 8 }, (_, i) => (
        <li key={i} className="h-48 animate-pulse rounded-xl border border-gray-200 bg-white p-4">
          <div className="h-4 w-20 rounded bg-gray-200" />
          <div className="mt-4 h-4 w-3/4 rounded bg-gray-200" />
          <div className="mt-2 h-3 w-1/2 rounded bg-gray-100" />
          <div className="mt-10 h-5 w-24 rounded bg-gray-200" />
        </li>
      ))}
    </ul>
  )
}
