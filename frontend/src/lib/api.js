/**
 * Modulul comun pentru apelurile către API-ul FastAPI.
 * Adresa vine din VITE_API_URL (vezi .env.example); implicit, serverul local de dezvoltare.
 */

export const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')

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
 * @param {string} [options.token]    token de autentificare (Bearer)
 */
export async function apiRequest(path, { method = 'GET', body, token, headers = {}, ...rest } = {}) {
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
