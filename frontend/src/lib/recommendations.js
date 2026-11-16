/**
 * Încărcarea recomandărilor (GET /recommendations) și a produselor similare (GET /products/{id}/similar).
 *
 *   const { status, data, error, reload } = useRecommendations({ k: 12, exclude: [productId] })
 *   const { status, data, error, reload } = useSimilarProducts(productId, 4)
 *
 * status: "loading" | "ready" | "error". Listele se reîncarcă singure când se schimbă contul
 * sau când o pagină anunță o schimbare a datelor utilizatorului (vezi userData.js).
 */
import { useEffect, useState } from 'react'
import { api } from './api.js'
import { useAuth } from './auth.jsx'
import { useUserDataVersion } from './userData.js'

function useApiResource(path, enabled) {
  const { token } = useAuth()
  const version = useUserDataVersion()
  const [reloadKey, setReloadKey] = useState(0)
  const [state, setState] = useState({ status: 'loading', data: null, error: null })

  useEffect(() => {
    if (!enabled) return
    let active = true
    // Datele vechi rămân vizibile (estompat) cât se încarcă cele noi.
    setState((current) => ({ ...current, status: 'loading', error: null }))
    api
      .get(path)
      .then((data) => active && setState({ status: 'ready', data, error: null }))
      .catch((error) => active && setState({ status: 'error', data: null, error }))
    return () => {
      active = false
    }
  }, [path, enabled, token, version, reloadKey])

  return { ...state, reload: () => setReloadKey((key) => key + 1) }
}

export function useRecommendations({ k = 12, exclude = [], enabled = true } = {}) {
  const params = new URLSearchParams({ k: String(k) })
  exclude.forEach((id) => params.append('exclude', String(id)))
  return useApiResource(`/recommendations?${params}`, enabled)
}

export function useSimilarProducts(productId, k = 4) {
  return useApiResource(`/products/${encodeURIComponent(productId)}/similar?k=${k}`, productId != null)
}
