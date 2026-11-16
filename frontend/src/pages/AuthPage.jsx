import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { AuthCard, FormError, SubmitButton, TextField } from '../components/Form.jsx'
import { errorMessage, fieldErrors } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'

export default function AuthPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/catalog'

  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [loading, setLoading] = useState(false)

  const update = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }))
    setErrors((current) => ({ ...current, [field]: undefined }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const clientErrors = {}
    if (!form.email.trim()) clientErrors.email = 'Introdu adresa de e-mail.'
    if (!form.password) clientErrors.password = 'Introdu parola.'
    setErrors(clientErrors)
    setFormError('')
    if (Object.keys(clientErrors).length) return

    setLoading(true)
    try {
      await login(form.email.trim(), form.password)
      navigate(from, { replace: true })
    } catch (error) {
      setErrors(fieldErrors(error))
      setFormError(errorMessage(error))
      setLoading(false)
    }
  }

  return (
    <AuthCard
      title="Autentificare"
      subtitle="Intră în contul tău HobbyShop ca să vezi recomandările personalizate."
      footer={
        <>
          Nu ai cont?{' '}
          <Link to="/inregistrare" className="font-medium text-emerald-700 hover:text-emerald-900">
            Creează unul
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <FormError>{formError}</FormError>
        <TextField
          id="email"
          label="E-mail"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={update('email')}
          error={errors.email}
          autoFocus
        />
        <TextField
          id="password"
          label="Parolă"
          type="password"
          autoComplete="current-password"
          value={form.password}
          onChange={update('password')}
          error={errors.password}
        />
        <SubmitButton loading={loading} loadingText="Se verifică…">
          Intră în cont
        </SubmitButton>
      </form>
    </AuthCard>
  )
}
