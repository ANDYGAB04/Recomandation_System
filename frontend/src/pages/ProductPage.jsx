import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import RecommendationList from '../components/RecommendationList.jsx'
import RecommendedStrip from '../components/RecommendedStrip.jsx'
import Spinner from '../components/Spinner.jsx'
import { AvailabilityBadge, EmptyState, ErrorState, TestDataBadge } from '../components/Status.jsx'
import { api, errorMessage } from '../lib/api.js'
import { formatPrice } from '../lib/format.js'
import { useSimilarProducts } from '../lib/recommendations.js'
import { useVocabulary } from '../lib/vocabulary.js'

export default function ProductPage() {
  const { id } = useParams()
  const location = useLocation()
  const { label } = useVocabulary()
  const [state, setState] = useState({ status: 'loading', product: null, error: null })
  const [reloadKey, setReloadKey] = useState(0)

  // „Înapoi la catalog” păstrează filtrele cu care s-a ajuns aici.
  const from = location.state?.from
  const backTo = from ? `${from.pathname}${from.search}` : '/catalog'

  useEffect(() => {
    let active = true
    setState({ status: 'loading', product: null, error: null })
    api
      .get(`/products/${encodeURIComponent(id)}`)
      .then((product) => active && setState({ status: 'ready', product, error: null }))
      .catch((error) => active && setState({ status: 'error', product: null, error }))
    return () => {
      active = false
    }
  }, [id, reloadKey])

  const backLink = (
    <Link to={backTo} className="inline-flex items-center gap-1 text-sm font-medium text-emerald-700 hover:text-emerald-900">
      ← Înapoi la catalog
    </Link>
  )

  if (state.status === 'loading') return <Spinner label="Se încarcă produsul…" />

  if (state.status === 'error') {
    const notFound = state.error?.status === 404 || state.error?.status === 422
    return (
      <section className="space-y-6">
        {backLink}
        <ErrorState
          title={notFound ? 'Produsul nu există.' : 'Nu am putut încărca produsul.'}
          message={notFound ? 'Poate a fost scos din catalog sau adresa e greșită.' : errorMessage(state.error)}
          onRetry={notFound ? undefined : () => setReloadKey((key) => key + 1)}
        />
      </section>
    )
  }

  const product = state.product
  const details = [
    { title: 'Activități', values: product.usages.map((v) => label('activities', v)) },
    { title: 'Nivel', values: product.levels.map((v) => label('levels', v)) },
    { title: 'Stil', values: product.styles.map((v) => label('styles', v)) },
    { title: 'Sezon', values: product.seasons.map((v) => label('seasons', v)) },
  ]

  return (
    <section className="space-y-8">
      {backLink}

      <article className="grid gap-6 rounded-xl border border-gray-200 bg-white p-5 shadow-sm sm:p-8 lg:grid-cols-[2fr_1fr]">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-800">
              {label('activities', product.category)}
            </span>
            {product.is_test_data && <TestDataBadge />}
          </div>
          <h1 className="mt-3 text-2xl font-semibold text-gray-900 sm:text-3xl">{product.name}</h1>
          <p className="mt-4 leading-relaxed text-gray-700">{product.description}</p>

          {product.tags.length > 0 && (
            <ul className="mt-5 flex flex-wrap gap-2" aria-label="Etichete">
              {product.tags.map((tag) => (
                <li key={tag} className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-700">
                  {tag}
                </li>
              ))}
            </ul>
          )}

          <dl className="mt-6 grid gap-4 sm:grid-cols-2">
            {details.map(({ title, values }) => (
              <div key={title}>
                <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</dt>
                <dd className="mt-1 text-sm text-gray-800">{values.length ? values.join(', ') : 'Oricare'}</dd>
              </div>
            ))}
          </dl>
        </div>

        <aside className="flex flex-col gap-3 rounded-lg bg-gray-50 p-5 lg:self-start">
          <p className="text-3xl font-semibold text-gray-900">{formatPrice(product.price)}</p>
          <AvailabilityBadge available={product.available} />
          <p className="text-xs text-gray-500">
            Produs fictiv, creat pentru demonstrație. Cumpărarea va fi simulată.
          </p>
          {/* Butoanele de favorite și cumpărare (simulată) se adaugă la pasul 19 (CRI-17). */}
        </aside>
      </article>

      <section id="produse-similare" aria-labelledby="produse-similare-titlu">
        <h2 id="produse-similare-titlu" className="text-lg font-semibold text-gray-900">
          Produse similare
        </h2>
        <div className="mt-3">
          <SimilarProducts productId={product.id} />
        </div>
      </section>

      {/* Produsul deschis nu apare în propriile recomandări. */}
      <RecommendedStrip exclude={[product.id]} />
    </section>
  )
}

function SimilarProducts({ productId }) {
  const similar = useSimilarProducts(productId, 4)
  return (
    <RecommendationList
      resource={similar}
      scoreLabel="Asemănare"
      emptyState={<EmptyState title="Nu am găsit produse asemănătoare." />}
    />
  )
}
