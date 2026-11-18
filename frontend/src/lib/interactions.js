
import { useEffect, useState } from 'react'
import { api } from './api.js'
import { useAuth } from './auth.jsx'
import { useUserDataVersion } from './userData.js'


export function newEventId() {
  if (globalThis.crypto?.randomUUID) return crypto.randomUUID()
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`
}


export function sendInteraction(productId, type, eventId = newEventId()) {
  return api.post('/interactions', { event_id: eventId, product_id: productId, type })
}


export function useHistory() {
  const { isAuthenticated, user } = useAuth()
  const version = useUserDataVersion()
  const [reloadKey, setReloadKey] = useState(0)
  const [state, setState] = useState({ status: 'loading', data: null, error: null })

  useEffect(() => {
    if (!isAuthenticated) {
      setState({ status: 'ready', data: null, error: null })
      return
    }
    let active = true
    setState((current) => ({ ...current, status: 'loading', error: null }))
    api
      .get('/me/history')
      .then((data) => active && setState({ status: 'ready', data, error: null }))
      .catch((error) => active && setState({ status: 'error', data: null, error }))
    return () => {
      active = false
    }
  }, [isAuthenticated, user?.id, version, reloadKey])

  return { ...state, reload: () => setReloadKey((key) => key + 1) }
}
