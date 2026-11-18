
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, setAuthToken, setUnauthorizedHandler } from './api.js'

const TOKEN_KEY = 'hobbyshop.token'

function readToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

function writeToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    
  }
}

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => {
    const saved = readToken()
    setAuthToken(saved) 
    return saved
  })
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState(token ? 'loading' : 'ready')

  const applyToken = useCallback((newToken) => {
    setAuthToken(newToken)
    writeToken(newToken)
    setToken(newToken)
  }, [])

  const logout = useCallback(() => {
    applyToken(null)
    setUser(null)
    setStatus('ready')
  }, [applyToken])

  
  useEffect(() => {
    setUnauthorizedHandler(logout)
    return () => setUnauthorizedHandler(null)
  }, [logout])

  
  useEffect(() => {
    if (!token || user) return
    let active = true
    api
      .get('/auth/me')
      .then((me) => active && setUser(me))
      
      .catch((error) => active && error.status === 401 && logout())
      .finally(() => active && setStatus('ready'))
    return () => {
      active = false
    }
  }, [token, user, logout])

  const startSession = useCallback(
    ({ access_token, user: account }) => {
      applyToken(access_token)
      setUser(account)
      setStatus('ready')
    },
    [applyToken],
  )

  const login = useCallback(
    async (email, password) => startSession(await api.post('/auth/login', { email, password })),
    [startSession],
  )

  const register = useCallback(
    async (data) => startSession(await api.post('/auth/register', data)),
    [startSession],
  )

  const value = useMemo(
    () => ({ user, token, status, isAuthenticated: Boolean(user), login, register, logout }),
    [user, token, status, login, register, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth trebuie folosit în interiorul <AuthProvider>.')
  return context
}
