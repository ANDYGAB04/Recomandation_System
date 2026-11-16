/**
 * Modulul comun pentru apelurile către API-ul FastAPI.
 * Adresa vine din VITE_API_URL (vezi .env.example); implicit, serverul local de dezvoltare.
 */

export const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')

// Token-ul utilizatorului autentificat, trimis automat la fiecare cerere (setat de AuthProvider).
let authToken = null
let onUnauthorized = null

export function setAuthToken(token) {
  authToken = token || null
}

/** Funcția apelată când API-ul răspunde 401 la o cerere trimisă cu token (token expirat sau invalid). */
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

export class ApiError extends Error {
  constructor(status, message, data) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

/**
 * Face o cerere către API și întoarce corpul răspunsului (JSON sau text; null pentru 204).
 * Aruncă ApiError pentru răspunsuri cu cod de eroare sau când API-ul nu răspunde (status 0).
 *
 * @param {string} path               calea, de exemplu "/health"
 * @param {object} [options]
 * @param {string} [options.method]   implicit "GET"
 * @param {any}    [options.body]     se trimite ca JSON
 * @param {string} [options.token]    token de autentificare (Bearer); implicit, cel al utilizatorului autentificat
 */
export async function apiRequest(path, { method = 'GET', body, token = authToken, headers = {}, ...rest } = {}) {
  const finalHeaders = { Accept: 'application/json', ...headers }
  if (body !== undefined) finalHeaders['Content-Type'] = 'application/json'
  if (token) finalHeaders.Authorization = `Bearer ${token}`

  let response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...rest,
      method,
      headers: finalHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch (error) {
    throw new ApiError(0, `API-ul nu răspunde la ${API_URL}`, error)
  }

  if (response.status === 204) return null
  const isJson = response.headers.get('content-type')?.includes('application/json')
  const data = isJson ? await response.json() : await response.text()

  if (!response.ok) {
    if (response.status === 401 && token && token === authToken) onUnauthorized?.()
    const message = (isJson && typeof data?.detail === 'string' && data.detail) || `Eroare ${response.status}`
    throw new ApiError(response.status, message, data)
  }
  return data
}

export const api = {
  get: (path, options) => apiRequest(path, { ...options, method: 'GET' }),
  post: (path, body, options) => apiRequest(path, { ...options, method: 'POST', body }),
  put: (path, body, options) => apiRequest(path, { ...options, method: 'PUT', body }),
  patch: (path, body, options) => apiRequest(path, { ...options, method: 'PATCH', body }),
  delete: (path, options) => apiRequest(path, { ...options, method: 'DELETE' }),
}

/** GET /health — verifică faptul că API-ul și baza de date răspund. */
export const getHealth = () => api.get('/health')

/**
 * Erorile de validare (422) pe câmpuri: { email: "…", password: "…" }.
 * FastAPI trimite în `detail` o listă cu `loc` (de exemplu ["body", "email"]) și `msg`.
 */
export function fieldErrors(error) {
  if (!(error instanceof ApiError) || error.status !== 422 || !Array.isArray(error.data?.detail)) return {}
  const errors = {}
  for (const item of error.data.detail) {
    const field = item.loc?.[item.loc.length - 1]
    if (typeof field === 'string' && !errors[field]) errors[field] = translateValidation(item)
  }
  return errors
}

function translateValidation(item) {
  const min = item.ctx?.min_length
  const max = item.ctx?.max_length
  switch (item.type) {
    case 'missing':
      return 'Câmpul este obligatoriu.'
    case 'string_too_short':
      return min > 1 ? `Minimum ${min} caractere.` : 'Câmpul este obligatoriu.'
    case 'string_too_long':
      return `Maximum ${max} caractere.`
    case 'value_error':
      return item.loc?.includes('email') ? 'Adresa de e-mail nu este validă.' : item.msg
    default:
      return item.msg
  }
}

/** Un mesaj de eroare lizibil, de afișat utilizatorului. */
export function errorMessage(error) {
  if (error instanceof ApiError) {
    if (error.status === 0) return 'Serverul nu răspunde. Verifică dacă backendul rulează.'
    if (error.status === 422) return 'Verifică datele introduse.'
    return error.message
  }
  return 'A apărut o eroare neașteptată.'
}
