import { useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { errorMessage } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'
import { sendInteraction } from '../lib/interactions.js'
import { notifyUserDataChanged } from '../lib/userData.js'

/**
 * Butoanele de pe pagina de produs: favorite și cumpărare simulată.
 * Starea vine din istoricul din backend (`history`), deci rămâne corectă după reîncărcare.
 * Cât timp o acțiune e în curs, butoanele sunt blocate: un dublu click trimite un singur eveniment.
 */
export default function ProductActions({ product, history }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  const busy = useRef(false) // blocare sincronă: al doilea click ajunge înainte de re-render
  const [pending, setPending] = useState(null) // "favorite" | "purchase" | null
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  // Rezultatul ultimei acțiuni, până sosește istoricul actualizat.
  const [local, setLocal] = useState({})

  if (!isAuthenticated) {
    return (
      <p className="rounded-md bg-white px-3 py-2 text-sm text-gray-600 ring-1 ring-gray-200">
        <Link to="/autentificare" state={{ from: location }} className="font-medium text-emerald-700 hover:text-emerald-900">
          Autentifică-te
        </Link>{' '}
        ca să salvezi produsul la favorite sau să-l cumperi (simulat).
      </p>
    )
  }

  const historyLoaded = history.status === 'ready' && history.data
  const isFavorite =
    local.favorite ?? Boolean(history.data?.favorites.some((p) => p.id === product.id))
  const purchased =
    local.purchased ?? Boolean(history.data?.purchases.some((p) => p.product.id === product.id))

  async function act(type, onSuccess) {
    if (busy.current) return
    busy.current = true
    setPending(type === 'purchase' ? 'purchase' : 'favorite')
    setError('')
    setMessage('')
    try {
      await sendInteraction(product.id, type)
      onSuccess()
      notifyUserDataChanged() // istoricul și recomandările se reîncarcă
    } catch (err) {
      if (err.status === 409 && type === 'purchase' && /deja/.test(err.message)) setLocal((l) => ({ ...l, purchased: true }))
      setError(errorMessage(err))
    } finally {
      busy.current = false
      setPending(null)
    }
  }

  const toggleFavorite = () =>
    act(isFavorite ? 'unfavorite' : 'favorite', () => {
      setLocal((l) => ({ ...l, favorite: !isFavorite }))
      setMessage(isFavorite ? 'Produsul a fost scos din favorite.' : 'Produsul a fost adăugat la favorite.')
    })

  const purchase = () =>
    act('purchase', () => {
      setLocal((l) => ({ ...l, purchased: true }))
      setMessage('Cumpărare simulată înregistrată. Nu s-a plătit nimic.')
    })

  const disabled = !historyLoaded || pending !== null
  const purchaseDisabled = disabled || purchased || !product.available
  const purchaseLabel = purchased
    ? '✓ Cumpărat'
    : !product.available
      ? 'Indisponibil'
      : pending === 'purchase'
        ? 'Se înregistrează…'
        : 'Cumpără (simulat)'

  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        onClick={purchase}
        disabled={purchaseDisabled}
        className="rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:cursor-not-allowed disabled:bg-gray-300 disabled:text-gray-600"
      >
        {purchaseLabel}
      </button>
      <button
        type="button"
        onClick={toggleFavorite}
        disabled={disabled}
        aria-pressed={isFavorite}
        className={`rounded-md border px-4 py-2.5 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:cursor-not-allowed disabled:opacity-60 ${
          isFavorite
            ? 'border-amber-300 bg-amber-50 text-amber-900 hover:bg-amber-100'
            : 'border-gray-300 bg-white text-gray-800 hover:border-emerald-600 hover:text-emerald-800'
        }`}
      >
        {pending === 'favorite' ? 'Se salvează…' : isFavorite ? '★ Scoate din favorite' : '☆ Adaugă la favorite'}
      </button>
      {history.status === 'error' && (
        <p className="text-xs text-red-600">
          Nu am putut încărca istoricul.{' '}
          <button type="button" onClick={history.reload} className="underline">
            Reîncearcă
          </button>
        </p>
      )}
      <p aria-live="polite" className="min-h-4 text-xs">
        {error ? <span className="text-red-600">{error}</span> : <span className="text-emerald-800">{message}</span>}
      </p>
    </div>
  )
}
