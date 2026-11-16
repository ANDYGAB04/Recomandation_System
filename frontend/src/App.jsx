import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import RequireAuth, { GuestOnly } from './components/RequireAuth.jsx'
import AuthPage from './pages/AuthPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import SettingsPage from './pages/SettingsPage.jsx'
import CatalogPage from './pages/CatalogPage.jsx'
import ProductPage from './pages/ProductPage.jsx'
import RecommendationsPage from './pages/RecommendationsPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import EvaluationPage from './pages/EvaluationPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/catalog" replace />} />

        {/* Publice */}
        <Route path="catalog" element={<CatalogPage />} />
        <Route path="produs/:id" element={<ProductPage />} />
        <Route path="evaluare" element={<EvaluationPage />} />

        {/* Doar pentru cine nu e autentificat */}
        <Route element={<GuestOnly />}>
          <Route path="autentificare" element={<AuthPage />} />
          <Route path="inregistrare" element={<RegisterPage />} />
        </Route>

        {/* Protejate: cer autentificare */}
        <Route element={<RequireAuth />}>
          <Route path="setari" element={<SettingsPage />} />
          <Route path="recomandari" element={<RecommendationsPage />} />
          <Route path="profil" element={<ProfilePage />} />
          <Route path="istoric" element={<HistoryPage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
