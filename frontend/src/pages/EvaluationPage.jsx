import Spinner from '../components/Spinner.jsx'
import { ErrorState } from '../components/Status.jsx'
import { errorMessage } from '../lib/api.js'
import { useApiResource } from '../lib/recommendations.js'

const number = new Intl.NumberFormat('ro-RO', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
const percentFormat = new Intl.NumberFormat('ro-RO', { style: 'percent', maximumFractionDigits: 1 })
const dateFormat = new Intl.DateTimeFormat('ro-RO', { day: 'numeric', month: 'long', timeZone: 'UTC' })

const formatMetric = (value) => (value == null ? '–' : number.format(value))
const formatPercent = (value) => (value == null ? '–' : percentFormat.format(value))
const formatMs = (value) => (value == null ? '–' : `${value.toLocaleString('ro-RO', { maximumFractionDigits: 2 })} ms`)

function formatPeriod({ start, end }) {
  // `end` este exclusiv: ultima zi inclusă este cea dinainte.
  const last = new Date(new Date(end).getTime() - 24 * 60 * 60 * 1000)
  return `${dateFormat.format(new Date(start))} – ${dateFormat.format(last)}`
}

const METRICS = [
  { key: 'precision_at_k', title: 'Precision@5', format: formatMetric },
  { key: 'recall_at_k', title: 'Recall@5', format: formatMetric },
  { key: 'coverage', title: 'Acoperire catalog', format: formatPercent },
  { key: 'latency_ms', title: 'Timp de răspuns', format: formatMs },
]

/** Rezultatele evaluării offline (GET /evaluation): popularitate vs. recomandarea bazată pe profil. */
export default function EvaluationPage() {
  const { status, data, error, reload } = useApiResource('/evaluation')

  const header = (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900">Evaluare</h1>
      <p className="mt-1 max-w-3xl text-sm text-gray-600">
        Cât de bine prezice sistemul ce vor cumpăra clienții: comparăm recomandarea bazată pe profil cu o metodă simplă,
        produsele cele mai cumpărate.
      </p>
    </div>
  )

  if (status === 'error') {
    const noData = error?.status === 503
    return (
      <section className="space-y-6">
        {header}
        <ErrorState
          title={noData ? 'Nu există încă date de evaluat.' : 'Nu am putut încărca evaluarea.'}
          message={errorMessage(error)}
          onRetry={reload}
        />
      </section>
    )
  }
  if (!data) {
    return (
      <section className="space-y-6">
        {header}
        <Spinner label="Se calculează evaluarea…" />
      </section>
    )
  }

  const test = data.test
  const popularity = test.results.find((row) => row.strategy === 'popular')
  const profile = test.results.find((row) => row.strategy === 'personalized')

  return (
    <section className="space-y-8">
      {header}

      <p role="note" className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        <span className="font-semibold">{data.note}</span> Istoricul vine de la 300 de clienți simulați, generați
        pentru demonstrație.
      </p>

      {popularity && profile && <Highlights popularity={popularity} profile={profile} />}

      <ResultsSection
        title={`Rezultatul final (test): ${formatPeriod(test)}`}
        description="Configurația folosită de aplicație, comparată cu popularitatea și cu ponderile inițiale."
        window={test}
        k={data.k}
      />

      <details className="group rounded-xl border border-gray-200 bg-white shadow-sm">
        <summary className="cursor-pointer list-none px-5 py-4 font-semibold text-gray-900 marker:hidden">
          <span className="mr-2 inline-block transition group-open:rotate-90">›</span>
          Alegerea ponderilor (validare): {formatPeriod(data.validation)}
          <span className="mt-1 block pl-5 text-sm font-normal text-gray-600">
            Toate combinațiile încercate. Am ales-o pe cea cu cel mai mare Recall@5: {data.selected_config}.
          </span>
        </summary>
        <div className="border-t border-gray-100 p-5">
          <ResultsTable window={data.validation} k={data.k} highlight={data.selected_config} />
        </div>
      </details>

      <Method k={data.k} />
    </section>
  )
}

function Highlights({ popularity, profile }) {
  const ratio = popularity.recall_at_k > 0 ? profile.recall_at_k / popularity.recall_at_k : null
  const cards = [
    {
      title: 'Produse relevante găsite (Recall@5)',
      profile: formatMetric(profile.recall_at_k),
      popularity: formatMetric(popularity.recall_at_k),
      note: ratio && ratio > 1 ? `de ${ratio.toLocaleString('ro-RO', { maximumFractionDigits: 1 })} ori mai multe` : null,
    },
    {
      title: 'Precizia primelor 5 (Precision@5)',
      profile: formatMetric(profile.precision_at_k),
      popularity: formatMetric(popularity.precision_at_k),
    },
    {
      title: 'Cât din catalog este recomandat',
      profile: formatPercent(profile.coverage),
      popularity: formatPercent(popularity.coverage),
    },
  ]
  return (
    <ul className="grid gap-4 md:grid-cols-3">
      {cards.map((card) => (
        <li key={card.title} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-gray-600">{card.title}</p>
          <div className="mt-3 flex items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Profil</p>
              <p className="text-3xl font-semibold text-gray-900 tabular-nums">{card.profile}</p>
            </div>
            <div className="text-right">
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Popularitate</p>
              <p className="text-xl font-semibold text-gray-500 tabular-nums">{card.popularity}</p>
            </div>
          </div>
          {card.note && <p className="mt-2 text-sm font-medium text-emerald-800">{card.note}</p>}
        </li>
      ))}
    </ul>
  )
}

function ResultsSection({ title, description, window, k }) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
      <p className="mt-1 text-sm text-gray-600">{description}</p>
      <div className="mt-4">
        <ResultsTable window={window} k={k} />
      </div>
    </section>
  )
}

function ResultsTable({ window, k, highlight }) {
  const isHighlighted = (row) => highlight && row.config === highlight
  return (
    <>
      {/* Desktop: tabel */}
      <div className="hidden md:block">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="py-2 pr-4 font-semibold">Configurație</th>
              {METRICS.map((m) => (
                <th key={m.key} className="py-2 pl-4 text-right font-semibold">
                  {m.title.replace('@5', `@${k}`)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {window.results.map((row) => (
              <tr key={row.config} className={isHighlighted(row) ? 'bg-emerald-50 font-medium' : ''}>
                <td className="py-2 pr-4 text-gray-900">
                  {row.config}
                  {isHighlighted(row) && <span className="ml-2 text-xs font-semibold text-emerald-700">aleasă</span>}
                </td>
                {METRICS.map((m) => (
                  <td key={m.key} className="py-2 pl-4 text-right tabular-nums text-gray-800">
                    {m.format(row[m.key])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Telefon: câte un card pe configurație */}
      <ul className="space-y-3 md:hidden">
        {window.results.map((row) => (
          <li key={row.config} className={`rounded-lg border p-3 ${isHighlighted(row) ? 'border-emerald-300 bg-emerald-50' : 'border-gray-200'}`}>
            <p className="text-sm font-medium text-gray-900">{row.config}</p>
            <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              {METRICS.map((m) => (
                <div key={m.key} className="flex justify-between gap-2">
                  <dt className="text-gray-500">{m.title.replace('@5', `@${k}`)}</dt>
                  <dd className="tabular-nums text-gray-900">{m.format(row[m.key])}</dd>
                </div>
              ))}
            </dl>
          </li>
        ))}
      </ul>

      <p className="mt-3 text-xs text-gray-500">
        {window.users_evaluated} clienți cu cumpărări în interval ({window.users_without_relevant} fără cumpărări, excluși
        din metrici). {window.users_without_history > 0 && `${window.users_without_history} dintre ei nu aveau istoric înainte și sunt raportați separat. `}
        Timpul de răspuns este media pentru o listă de recomandări.
      </p>
    </>
  )
}

function Method({ k }) {
  const items = [
    ['Date', 'Istoricul pe 90 de zile al clienților simulați, împărțit în ordine cronologică: antrenare (primele 60 de zile), validare (următoarele 15), test (ultimele 15).'],
    ['Fără informații din viitor', 'Pentru fiecare interval, profilul din comportament și popularitatea se calculează doar din evenimentele de dinainte.'],
    ['Relevant', 'Un produs cumpărat de client în interval, încă disponibil și necumpărat înainte.'],
    [`Precision@${k}`, `Câte dintre primele ${k} recomandări sunt relevante, în medie.`],
    [`Recall@${k}`, `Câte dintre produsele relevante apar în primele ${k} recomandări, în medie.`],
    ['Acoperire', 'Ce parte din catalogul disponibil apare în recomandări, pentru toți clienții evaluați.'],
    ['Ponderi', 'α (cât contează setările față de comportament) și ponderile acțiunilor se aleg pe validare; testul doar raportează rezultatul.'],
  ]
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900">Cum am evaluat</h2>
      <dl className="mt-4 grid gap-4 sm:grid-cols-2">
        {items.map(([title, text]) => (
          <div key={title}>
            <dt className="text-sm font-semibold text-gray-900">{title}</dt>
            <dd className="mt-1 text-sm text-gray-600">{text}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
