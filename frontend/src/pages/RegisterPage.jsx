import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AuthCard, FormError, SubmitButton, TextField } from '../components/Form.jsx'
import { errorMessage, fieldErrors } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'

const MIN_PASSWORD = 8
const EMPTY = { display_name: '', email: '', password: '', confirm: '' }

function validate(form) {
  const errors = {}
  if (!form.display_name.trim()) errors.display_name = 'Introdu numele afișat.'
  else if (form.display_name.trim().length > 100) errors.display_name = 'Maximum 100 de caractere.'
  if (!form.email.trim()) errors.email = 'Introdu adresa de e-mail.'
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) errors.email = 'Adresa de e-mail nu este validă.'
  if (form.password.length < MIN_PASSWORD) errors.password = `Parola trebuie să aibă cel puțin ${MIN_PASSWORD} caractere.`
  if (form.confirm !== form.password) errors.confirm = 'Parolele nu coincid.'
  return errors
}

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState(EMPTY)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [loading, setLoading] = useState(false)

  const update = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }))
    setErrors((current) => ({ ...current, [field]: undefined }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const clientErrors = validate(form)
    setErrors(clientErrors)
    setFormError('')
    if (Object.keys(clientErrors).length) return

    setLoading(true)
    try {
      await register({ email: form.email.trim(), password: form.password, display_name: form.display_name.trim() })
      
      navigate('/setari', { replace: true, state: { newAccount: true } })
    } catch (error) {
      const apiErrors = fieldErrors(error)
      if (error.status === 409) apiErrors.email = error.message
      setErrors(apiErrors)
      setFormError(errorMessage(error))
      setLoading(false)
    }
  }

  return (
    <AuthCard
      title="Creează un cont"
      subtitle="După creare îți completezi setările de profil, iar recomandările apar imediat."
      footer={
        <>
          Ai deja cont?{' '}
          <Link to="/autentificare" className="font-medium text-emerald-700 hover:text-emerald-900">
            Autentifică-te
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <FormError>{formError}</FormError>
        <TextField
          id="display_name"
          label="Nume afișat"
          autoComplete="nickname"
          value={form.display_name}
          onChange={update('display_name')}
          error={errors.display_name}
          maxLength={100}
          autoFocus
        />
        <TextField
          id="email"
          label="E-mail"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={update('email')}
          error={errors.email}
        />
        <TextField
          id="password"
          label="Parolă"
          type="password"
          autoComplete="new-password"
          value={form.password}
          onChange={update('password')}
          error={errors.password}
          hint={`Cel puțin ${MIN_PASSWORD} caractere.`}
        />
        <TextField
          id="confirm"
          label="Confirmă parola"
          type="password"
          autoComplete="new-password"
          value={form.confirm}
          onChange={update('confirm')}
          error={errors.confirm}
        />
        <SubmitButton loading={loading} loadingText="Se creează contul…">
          Creează contul
        </SubmitButton>
      </form>
    </AuthCard>
  )
}
