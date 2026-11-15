import { useParams } from 'react-router-dom'
import PagePlaceholder from '../components/PagePlaceholder.jsx'

export default function ProductPage() {
  const { id } = useParams()
  return <PagePlaceholder title={`Produs #${id}`} step="pasul 15" />
}
