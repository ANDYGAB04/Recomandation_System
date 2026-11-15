import { Link } from 'react-router-dom'
import PagePlaceholder from '../components/PagePlaceholder.jsx'

export default function NotFoundPage() {
  return (
    <PagePlaceholder title="Pagina nu există">
      <Link to="/catalog" className="text-emerald-700 underline hover:text-emerald-900">
        Înapoi la catalog
      </Link>
    </PagePlaceholder>
  )
}
