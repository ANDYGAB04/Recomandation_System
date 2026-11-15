import { NavLink, Outlet } from 'react-router-dom'
import ApiStatus from './ApiStatus.jsx'

const mainLinks = [
  { to: '/catalog', label: 'Catalog' },
  { to: '/recomandari', label: 'Recomandări' },
  { to: '/profil', label: 'Profilul meu' },
  { to: '/setari', label: 'Setări' },
  { to: '/evaluare', label: 'Evaluare' },
]

const authLinks = [
  { to: '/autentificare', label: 'Autentificare' },
  { to: '/inregistrare', label: 'Înregistrare' },
]

function navClass({ isActive }) {
  return `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? 'bg-emerald-700 text-white' : 'text-gray-700 hover:bg-emerald-50 hover:text-emerald-800'
  }`
}

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-gray-50 text-gray-900">
      <header className="border-b border-gray-200 bg-white">
        <nav className="mx-auto flex max-w-6xl flex-wrap items-center gap-2 px-4 py-3">
          <NavLink to="/catalog" className="mr-4 text-lg font-bold text-emerald-800">
            HobbyShop
          </NavLink>
          {mainLinks.map((link) => (
            <NavLink key={link.to} to={link.to} className={navClass}>
              {link.label}
            </NavLink>
          ))}
          <div className="ml-auto flex items-center gap-2">
            <ApiStatus />
            {authLinks.map((link) => (
              <NavLink key={link.to} to={link.to} className={navClass}>
                {link.label}
              </NavLink>
            ))}
          </div>
        </nav>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-gray-200 bg-white py-4 text-center text-xs text-gray-500">
        HobbyShop · magazin demonstrativ: toate produsele, conturile și cumpărăturile sunt date de test.
      </footer>
    </div>
  )
}
