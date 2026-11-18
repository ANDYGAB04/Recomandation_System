import { Link } from 'react-router-dom'
import RecommendationList from './RecommendationList.jsx'
import { useAuth } from '../lib/auth.jsx'
import { useRecommendations } from '../lib/recommendations.js'


export default function RecommendedStrip({ title = 'Recomandate pentru tine', count = 4, exclude = [] }) {
  const { isAuthenticated, status } = useAuth()
  const recommendations = useRecommendations({ k: count, exclude, enabled: isAuthenticated })

  if (status === 'loading') return null
  if (!isAuthenticated) {
    return (
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-4 text-sm text-emerald-900">
        <p>
          <span className="font-semibold">Recomandări personalizate:</span> spune-ne ce activități practici și îți
          arătăm echipamentul potrivit.
        </p>
        <div className="flex gap-2">
          <Link to="/inregistrare" className="rounded-md bg-emerald-700 px-3 py-1.5 font-semibold text-white hover:bg-emerald-800">
            Creează cont
          </Link>
          <Link to="/autentificare" className="rounded-md bg-white px-3 py-1.5 font-medium text-emerald-800 ring-1 ring-emerald-200 hover:bg-emerald-100">
            Autentificare
          </Link>
        </div>
      </div>
    )
  }

  return (
    <section aria-labelledby="recomandate-titlu">
      <div className="flex items-baseline justify-between gap-3">
        <h2 id="recomandate-titlu" className="text-lg font-semibold text-gray-900">
          {title}
        </h2>
        <Link to="/recomandari" className="text-sm font-medium text-emerald-700 hover:text-emerald-900">
          Vezi toate →
        </Link>
      </div>
      <div className="mt-3">
        <RecommendationList resource={recommendations} skeletonCount={count} withFeedback />
      </div>
    </section>
  )
}
