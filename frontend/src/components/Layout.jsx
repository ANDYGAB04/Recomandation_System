import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth.jsx'
import ApiStatus from './ApiStatus.jsx'

const publicLinks = [
  { to: '/catalog', label: 'Catalog' },
  { to: '/evaluare', label: 'Evaluare' },
]

const privateLinks = [
  { to: '/recomandari', label: 'Recomandări' },
  { to: '/profil', label: 'Profilul meu' },
  { to: '/setari', label: 'Setări' },
]

const guestLinks = [
  { to: '/autentificare', label: 'Autentificare' },
  { to: '/inregistrare', label: 'Înregistrare' },
]

function navClass({ isActive }) {
  return `block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? 'bg-emerald-700 text-white' : 'text-gray-700 hover:bg-emerald-50 hover:text-emerald-800'
  }`
}

export default function Layout() {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  // Meniul de pe telefon se închide după navigare.
  useEffect(() => setMenuOpen(false), [location.pathname])

  const mainLinks = isAuthenticated
    ? [publicLinks[0], ...privateLinks, publicLinks[1]]
    : publicLinks

  function handleLogout() {
    logout()
    navigate('/autentificare', { replace: true })
  }

  const account = isAuthenticated ? (
    <div className="flex flex-col gap-2 md:flex-row md:items-center">
      <span className="px-3 text-sm text-gray-600 md:px-0" title={user.email}>
        Salut, <span className="font-semibold text-gray-900">{user.display_name}</span>
      </span>
      <button
        type="button"
        onClick={handleLogout}
        className="rounded-md border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 transition hover:border-emerald-600 hover:text-emerald-800"
      >
        Deconectare
      </button>
    </div>
  ) : (
    guestLinks.map((link) => (
      <NavLink key={link.to} to={link.to} className={navClass}>
        {link.label}
      </NavLink>
    ))
  )

  return (
    <div className="flex min-h-screen flex-col bg-gray-50 text-gray-900">
      <header className="border-b border-gray-200 bg-white">
        <nav className="mx-auto max-w-6xl px-4 py-3">
          <div className="flex items-center gap-2">
            <NavLink to="/catalog" className="mr-4 text-lg font-bold text-emerald-800">
              HobbyShop
            </NavLink>

            <div className="hidden items-center gap-1 md:flex">
              {mainLinks.map((link) => (
                <NavLink key={link.to} to={link.to} className={navClass}>
                  {link.label}
                </NavLink>
              ))}
            </div>

            <div className="ml-auto hidden items-center gap-3 md:flex">
              <ApiStatus />
              {account}
            </div>

            <button
              type="button"
              className="ml-auto rounded-md p-2 text-gray-700 hover:bg-gray-100 md:hidden"
              aria-label={menuOpen ? 'Închide meniul' : 'Deschide meniul'}
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                {menuOpen ? (
                  <path strokeLinecap="round" d="M6 6l12 12M18 6L6 18" />
                ) : (
                  <path strokeLinecap="round" d="M4 7h16M4 12h16M4 17h16" />
                )}
              </svg>
            </button>
          </div>

          {menuOpen && (
            <div className="mt-3 flex flex-col gap-1 border-t border-gray-100 pt-3 md:hidden">
              {mainLinks.map((link) => (
                <NavLink key={link.to} to={link.to} className={navClass}>
                  {link.label}
                </NavLink>
              ))}
              <div className="mt-2 flex flex-col gap-1 border-t border-gray-100 pt-3">
                {account}
                <div className="px-3 pt-2">
                  <ApiStatus />
                </div>
              </div>
            </div>
          )}
        </nav>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-gray-200 bg-white px-4 py-4 text-center text-xs text-gray-500">
        HobbyShop · magazin demonstrativ: toate produsele, conturile și cumpărăturile sunt date de test.
      </footer>
    </div>
  )
}
