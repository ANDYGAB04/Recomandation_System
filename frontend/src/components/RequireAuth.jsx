import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth.jsx'
import Spinner from './Spinner.jsx'

/** Rute protejate: fără autentificare, utilizatorul ajunge la pagina de autentificare și revine după. */
export default function RequireAuth() {
  const { status, isAuthenticated } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <Spinner label="Se încarcă contul…" />
  if (!isAuthenticated) return <Navigate to="/autentificare" replace state={{ from: location }} />
  return <Outlet />
}

/** Paginile de autentificare și înregistrare nu au sens pentru cine e deja autentificat. */
export function GuestOnly() {
  const { status, isAuthenticated } = useAuth()
  if (status === 'loading') return <Spinner label="Se încarcă contul…" />
  if (isAuthenticated) return <Navigate to="/catalog" replace />
  return <Outlet />
}
