
import { useEffect, useSyncExternalStore } from 'react'
import { api, errorMessage } from './api.js'
import { useAuth } from './auth.jsx'

let state = { owner: null, status: 'idle', votes: {}, pending: {}, errors: {} }
let loading = null
const listeners = new Set()

function setState(changes) {
  state = { ...state, ...changes }
  listeners.forEach((listener) => listener())
}

function subscribe(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}


function ensureLoaded(owner) {
  
  if (state.owner === owner && (state.status === 'loading' || state.status === 'ready')) return
  setState({ owner, status: 'loading', votes: {}, pending: {}, errors: {} })
  const request = api.get('/recommendations/feedback')
  loading = request
  request
    .then((items) => {
      if (loading !== request) return 
      const votes = {}
      for (const item of items) votes[item.product_id] = item.useful
      setState({ status: 'ready', votes })
    })
    .catch(() => loading === request && setState({ status: 'error' }))
}

async function sendVote(productId, useful, strategy) {
  if (state.pending[productId]) return 
  const previous = state.votes[productId]
  if (previous === useful) return
  setState({
    votes: { ...state.votes, [productId]: useful },
    pending: { ...state.pending, [productId]: true },
    errors: { ...state.errors, [productId]: null },
  })
  try {
    await api.post('/recommendations/feedback', { product_id: productId, useful, strategy })
    setState({ pending: { ...state.pending, [productId]: false } })
  } catch (error) {
    const votes = { ...state.votes }
    if (previous === undefined) delete votes[productId]
    else votes[productId] = previous
    setState({
      votes,
      pending: { ...state.pending, [productId]: false },
      errors: { ...state.errors, [productId]: errorMessage(error) },
    })
  }
}

export function useFeedbackVote(productId) {
  const { user } = useAuth()
  const snapshot = useSyncExternalStore(subscribe, () => state)

  useEffect(() => {
    if (user) ensureLoaded(user.id)
  }, [user])

  const mine = user && snapshot.owner === user.id
  return {
    enabled: Boolean(user),
    loaded: mine && snapshot.status === 'ready',
    vote: mine ? snapshot.votes[productId] : undefined, 
    pending: mine && Boolean(snapshot.pending[productId]),
    error: mine ? snapshot.errors[productId] : null,
    send: (useful, strategy) => sendVote(productId, useful, strategy),
  }
}
