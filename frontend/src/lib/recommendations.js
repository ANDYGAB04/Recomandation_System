
import { useEffect, useState } from 'react'
import { api } from './api.js'
import { useAuth } from './auth.jsx'
import { useUserDataVersion } from './userData.js'

export function useApiResource(path, enabled = true) {
  const { token } = useAuth()
  const version = useUserDataVersion()
  const [reloadKey, setReloadKey] = useState(0)
  const [state, setState] = useState({ status: 'loading', data: null, error: null })

  useEffect(() => {
    if (!enabled) return
    let active = true
    
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

export function useRecommendationProfile() {
  return useApiResource('/recommendations/profile')
}
