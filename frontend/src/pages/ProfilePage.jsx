import { Link } from 'react-router-dom'
import Spinner from '../components/Spinner.jsx'
import { EmptyState, ErrorState } from '../components/Status.jsx'
import { errorMessage } from '../lib/api.js'
import { formatPrice } from '../lib/format.js'
import { useApiResource, useRecommendationProfile } from '../lib/recommendations.js'
import { useVocabulary } from '../lib/vocabulary.js'

const GROUP_LABELS = { activities: 'Activitate', styles: 'Stil', levels: 'Nivel', seasons: 'Sezon' }

const EVENTS = {
  purchase: { label: 'Cumpărături', badge: 'Cumpărat', color: 'bg-emerald-700', badgeClass: 'bg-emerald-100 text-emerald-800' },
  favorite: { label: 'Favorite', badge: 'Favorit', color: 'bg-emerald-500', badgeClass: 'bg-amber-100 text-amber-800' },
  view: { label: 'Vizualizări', badge: 'Văzut', color: 'bg-emerald-300', badgeClass: 'bg-gray-100 text-gray-700' },
}

const percent = (value) => `${Math.round(value * 100)}%`

/**
 * Pe ce date se bazează recomandările: setările față de comportament, interesele dominante,
 * setările alese și produsele din istoric. Utilă la prezentare: arată că recomandarea vine din profil.
 */
export default function ProfilePage() {
  const summary = useRecommendationProfile()
  const settings = useApiResource('/profile')
  const { data, error, status } = summary

  const header = (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Profilul meu de recomandare</h1>
        <p className="mt-1 max-w-2xl text-sm text-gray-600">
          Datele pe care se bazează recomandările tale: preferințele din setări și produsele pe care le vezi, le
          salvezi și le cumperi.
        </p>
      </div>
      <div className="flex gap-2 text-sm">
        <Link to="/recomandari" className="rounded-md px-3 py-2 font-medium text-emerald-700 hover:bg-emerald-50 hover:text-emerald-900">
          Vezi recomandările
        </Link>
        <Link to="/setari" className="rounded-md px-3 py-2 font-medium text-emerald-700 hover:bg-emerald-50 hover:text-emerald-900">
          Schimbă setările
        </Link>
      </div>
    </div>
  )

  if (status === 'error') {
    return (
      <section className="space-y-6">
        {header}
        <ErrorState title="Nu am putut încărca profilul de recomandare." message={errorMessage(error)} onRetry={summary.reload} />
      </section>
    )
  }
  if (!data) {
    return (
      <section className="space-y-6">
        {header}
        <Spinner label="Se încarcă profilul…" />
      </section>
    )
  }

  const empty = data.interests.length === 0 && data.top_products.length === 0
  return (
    <section className="space-y-6">
      {header}
      {empty ? (
        <EmptyState
          title="Profilul tău de recomandare este încă gol."
          message="Completează setările de profil sau explorează catalogul: recomandările se formează din preferințele tale și din produsele pe care le vezi, le salvezi și le cumperi."
          action={
            <div className="flex flex-wrap justify-center gap-2">
              <Link to="/setari" className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800">
                Completează setările
              </Link>
              <Link to="/catalog" className="rounded-md bg-white px-4 py-2 text-sm font-medium text-emerald-800 ring-1 ring-emerald-200 hover:bg-emerald-50">
                Mergi la catalog
              </Link>
            </div>
          }
        />
      ) : (
        <div className={`grid gap-6 lg:grid-cols-2 ${status === 'loading' ? 'opacity-60 transition-opacity' : ''}`} aria-busy={status === 'loading'}>
          <Sources data={data} />
          <Interests interests={data.interests} />
          <DeclaredSettings resource={settings} />
          <TopProducts products={data.top_products} />
        </div>
      )}
    </section>
  )
}

function Card({ title, description, children }) {
  return (
    <article className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h2 className="text-base font-semibold text-gray-900">{title}</h2>
      {description && <p className="mt-1 text-sm text-gray-600">{description}</p>}
      <div className="mt-4">{children}</div>
    </article>
  )
}

function Bar({ value, color = 'bg-emerald-600' }) {
  return (
    <div className="h-2.5 w-full overflow-hidden rounded-full bg-gray-100">
      <div className={`h-full rounded-full ${color}`} style={{ width: percent(Math.min(1, value)) }} />
    </div>
  )
}

function Sources({ data }) {
  const { declared, behavior } = data.sources
  const breakdown = Object.entries(EVENTS)
    .map(([event, info]) => ({ event, ...info, share: (data.behavior_breakdown[event] ?? 0) * behavior }))
    .filter((part) => part.share > 0)

  return (
    <Card
      title="Din ce se formează profilul"
      description="Recomandările combină setările tale cu ce faci în aplicație. Cumpărăturile contează cel mai mult, apoi favoritele, apoi vizualizările."
    >
      {/* Bara întreagă = 100% din profil */}
      <div className="flex h-4 w-full overflow-hidden rounded-full bg-gray-100" role="img" aria-label={`Setări ${percent(declared)}, comportament ${percent(behavior)}`}>
        {declared > 0 && <div className="h-full bg-sky-600" style={{ width: percent(declared) }} />}
        {breakdown.map((part) => (
          <div key={part.event} className={`h-full ${part.color}`} style={{ width: percent(part.share) }} />
        ))}
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <Legend color="bg-sky-600" label="Setări" value={declared} />
        {breakdown.map((part) => (
          <Legend key={part.event} color={part.color} label={part.label} value={part.share} />
        ))}
      </dl>
      {declared === 0 && (
        <p className="mt-4 text-sm text-gray-600">
          Nu ai completat încă setările.{' '}
          <Link to="/setari" className="font-medium text-emerald-700 underline hover:text-emerald-900">
            Completează-le
          </Link>{' '}
          pentru recomandări mai potrivite.
        </p>
      )}
    </Card>
  )
}

function Legend({ color, label, value }) {
  return (
    <div>
      <dt className="flex items-center gap-1.5 text-gray-600">
        <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
        {label}
      </dt>
      <dd className="mt-0.5 text-lg font-semibold text-gray-900">{percent(value)}</dd>
    </div>
  )
}

function Interests({ interests }) {
  const max = Math.max(...interests.map((i) => i.weight), 0)
  return (
    <Card title="Interesele tale dominante" description="Preferințele care contează cel mai mult când îți alegem produsele.">
      {interests.length === 0 ? (
        <p className="text-sm text-gray-600">Încă nu avem destule date.</p>
      ) : (
        <ul className="space-y-3">
          {interests.map((interest) => (
            <li key={`${interest.group}-${interest.value}`}>
              <div className="flex items-baseline justify-between gap-3 text-sm">
                <span className="font-medium text-gray-900">
                  {interest.label}
                  <span className="ml-2 text-xs font-normal text-gray-500">{GROUP_LABELS[interest.group] ?? interest.group}</span>
                </span>
                <span className="tabular-nums text-gray-600">{percent(interest.weight)}</span>
              </div>
              {/* Bara relativă la cel mai important interes, ca diferențele să se vadă ușor. */}
              <div className="mt-1">
                <Bar value={max > 0 ? interest.weight / max : 0} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

function DeclaredSettings({ resource }) {
  const { label } = useVocabulary()
  const { data, error, reload } = resource
  if (error) return <ErrorState title="Nu am putut încărca setările." message={errorMessage(error)} onRetry={reload} />

  const activities = Object.entries(data?.activities ?? {})
  const rows = data && [
    {
      title: 'Activități',
      value: activities.map(([activity, intensity]) => `${label('activities', activity)} (${label('intensities', intensity).toLowerCase()})`).join(', '),
    },
    { title: 'Nivel', value: data.level && label('levels', data.level) },
    { title: 'Stil', value: data.styles.map((s) => label('styles', s)).join(', ') },
    { title: 'Sezon', value: data.season && label('seasons', data.season) },
    { title: 'Buget maxim', value: data.max_budget != null && `${formatPrice(data.max_budget)} per produs` },
  ]

  return (
    <Card title="Ce ai ales în setări" description="Datele declarate de tine; le poți schimba oricând.">
      {!data ? (
        <Spinner label="Se încarcă setările…" />
      ) : (
        <>
          <dl className="divide-y divide-gray-100 text-sm">
            {rows.map(({ title, value }) => (
              <div key={title} className="flex justify-between gap-4 py-2">
                <dt className="text-gray-600">{title}</dt>
                <dd className={`text-right ${value ? 'font-medium text-gray-900' : 'text-gray-400'}`}>{value || 'Necompletat'}</dd>
              </div>
            ))}
          </dl>
          <Link to="/setari" className="mt-4 inline-block text-sm font-medium text-emerald-700 hover:text-emerald-900">
            Schimbă setările →
          </Link>
        </>
      )}
    </Card>
  )
}

function TopProducts({ products }) {
  return (
    <Card
      title="Produsele care îți influențează recomandările"
      description="Din istoricul tău, cele cu cea mai mare pondere: cumpărare = 10, favorit = 5, vizualizare = 1 (cel mult 3 per produs)."
    >
      {products.length === 0 ? (
        <p className="text-sm text-gray-600">
          Încă nu ai văzut, salvat sau cumpărat produse.{' '}
          <Link to="/catalog" className="font-medium text-emerald-700 underline hover:text-emerald-900">
            Explorează catalogul
          </Link>
          .
        </p>
      ) : (
        <ol className="divide-y divide-gray-100">
          {products.map(({ product, weight, events }) => (
            <li key={product.id} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
              <Link to={`/produs/${product.id}`} className="text-sm font-medium text-gray-900 hover:text-emerald-800">
                {product.name}
              </Link>
              <span className="flex items-center gap-1.5">
                {events.map((event) => (
                  <span key={event} className={`rounded-full px-2 py-0.5 text-xs font-medium ${EVENTS[event]?.badgeClass ?? 'bg-gray-100 text-gray-700'}`}>
                    {EVENTS[event]?.badge ?? event}
                  </span>
                ))}
                <span className="w-12 text-right text-xs tabular-nums text-gray-500" title="Ponderea în profil">
                  {weight} p
                </span>
              </span>
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}
