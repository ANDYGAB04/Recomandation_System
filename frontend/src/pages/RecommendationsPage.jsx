import { Link } from 'react-router-dom'
import RecommendationList from '../components/RecommendationList.jsx'
import { EmptyState, TestDataBadge } from '../components/Status.jsx'
import { useRecommendations } from '../lib/recommendations.js'

const COUNT = 12

export default function RecommendationsPage() {
  const recommendations = useRecommendations({ k: COUNT })

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Recomandate pentru tine</h1>
          <p className="mt-1 max-w-2xl text-sm text-gray-600">
            Alese pe baza setărilor din profilul tău și a produselor pe care le vezi, le salvezi și le cumperi.
            Sub fiecare produs scrie de ce ți-l recomandăm. <TestDataBadge className="align-middle" />
          </p>
        </div>
        <div className="flex gap-2 text-sm">
          <Link to="/profil" className="rounded-md px-3 py-2 font-medium text-emerald-700 hover:bg-emerald-50 hover:text-emerald-900">
            De ce văd aceste produse?
          </Link>
          <Link to="/setari" className="rounded-md px-3 py-2 font-medium text-emerald-700 hover:bg-emerald-50 hover:text-emerald-900">
            Schimbă setările
          </Link>
        </div>
      </div>

      <p className="mt-4 rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900">
        <span className="font-semibold">Participi la evaluare?</span> Votează „Ți-a fost utilă?” sub recomandări, apoi{' '}
        <Link to="/chestionar" className="font-semibold underline hover:text-sky-950">
          completează chestionarul
        </Link>{' '}
        (2 minute, anonim).
      </p>

      <div className="mt-6">
        <RecommendationList
          resource={recommendations}
          skeletonCount={8}
          withFeedback
          emptyState={
            <EmptyState
              title="Niciun produs nu se potrivește profilului tău."
              message="Poate bugetul maxim este prea mic sau ai cumpărat deja produsele potrivite. Încearcă alte setări."
              action={
                <Link to="/setari" className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800">
                  Mergi la setări
                </Link>
              }
            />
          }
        />
      </div>
    </section>
  )
}
