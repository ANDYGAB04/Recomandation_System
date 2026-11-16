import { useLocation } from 'react-router-dom'
import PagePlaceholder from '../components/PagePlaceholder.jsx'
import { useAuth } from '../lib/auth.jsx'

export default function SettingsPage() {
  const { user } = useAuth()
  const newAccount = useLocation().state?.newAccount

  return (
    <>
      {newAccount && (
        <div className="mb-6 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          Bun venit, <span className="font-semibold">{user?.display_name}</span>! Contul a fost creat. Completează
          setările de profil ca să primești recomandări personalizate.
        </div>
      )}
      <PagePlaceholder title="Setări" step="pasul 17" />
    </>
  )
}
