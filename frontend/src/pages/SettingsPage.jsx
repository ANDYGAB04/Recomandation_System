import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { FormError } from '../components/Form.jsx'
import Spinner from '../components/Spinner.jsx'
import { ErrorState } from '../components/Status.jsx'
import { ApiError, api, errorMessage } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'
import { notifyUserDataChanged } from '../lib/userData.js'
import { useVocabulary } from '../lib/vocabulary.js'

// ---------- Profil (API) ⇄ formular ----------

function toForm(profile) {
  return {
    activities: { ...profile.activities }, // { running: "high" }
    level: profile.level ?? '',
    styles: [...profile.styles],
    season: profile.season ?? '',
    max_budget: profile.max_budget == null ? '' : String(profile.max_budget),
  }
}

function toPayload(form) {
  const budget = form.max_budget.trim()
  return {
    activities: form.activities,
    level: form.level || null,
    styles: form.styles,
    season: form.season || null,
    max_budget: budget === '' ? null : Number(budget.replace(',', '.')),
  }
}

/** Cheie de comparație care nu depinde de ordinea activităților sau a stilurilor. */
function sameSettingsKey(form) {
  const payload = toPayload(form)
  return JSON.stringify({
    ...payload,
    activities: Object.entries(payload.activities).sort(),
    styles: [...payload.styles].sort(),
  })
}

function validate(form) {
  const errors = {}
  const budget = form.max_budget.trim()
  if (budget !== '') {
    const value = Number(budget.replace(',', '.'))
    if (!Number.isFinite(value) || value <= 0) errors.max_budget = 'Bugetul trebuie să fie un număr mai mare decât 0.'
  }
  return errors
}

/** Erorile 422 de la PUT /profile, pe câmpurile formularului (loc: ["body", "activities", "running"]). */
function profileFieldErrors(error) {
  if (!(error instanceof ApiError) || error.status !== 422 || !Array.isArray(error.data?.detail)) return {}
  const messages = {
    greater_than: 'Bugetul trebuie să fie mai mare decât 0.',
    enum: 'Valoare necunoscută.',
    extra_forbidden: 'Câmp necunoscut.',
  }
  const errors = {}
  for (const item of error.data.detail) {
    const field = item.loc?.[0] === 'body' ? item.loc[1] : undefined
    if (typeof field === 'string' && !errors[field]) errors[field] = messages[item.type] ?? item.msg.replace(/^Value error, /, '')
  }
  return errors
}

// ---------- Componente ----------

function Section({ title, description, error, children }) {
  return (
    <fieldset className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <legend className="sr-only">{title}</legend>
      <h2 className="text-base font-semibold text-gray-900" aria-hidden="true">
        {title}
      </h2>
      {description && <p className="mt-1 text-sm text-gray-600">{description}</p>}
      <div className="mt-4">{children}</div>
      {error && (
        <p role="alert" className="mt-3 text-sm text-red-600">
          {error}
        </p>
      )}
    </fieldset>
  )
}

function Choice({ selected, onClick, children, type = 'radio' }) {
  return (
    <button
      type="button"
      role={type}
      aria-checked={selected}
      onClick={onClick}
      className={`rounded-lg border px-3 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-emerald-300 ${
        selected
          ? 'border-emerald-700 bg-emerald-700 text-white'
          : 'border-gray-300 bg-white text-gray-700 hover:border-emerald-600 hover:text-emerald-800'
      }`}
    >
      {children}
    </button>
  )
}

// ---------- Pagina ----------

export default function SettingsPage() {
  const { user } = useAuth()
  const newAccount = useLocation().state?.newAccount
  const { options } = useVocabulary()

  const [load, setLoad] = useState({ status: 'loading', error: null })
  const [reloadKey, setReloadKey] = useState(0)
  const [form, setForm] = useState(null)
  const [saved, setSaved] = useState(null) // ultimul profil salvat (pentru „modificări nesalvate”)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)
  const [confirmation, setConfirmation] = useState(false)

  useEffect(() => {
    let active = true
    setLoad({ status: 'loading', error: null })
    api
      .get('/profile')
      .then((profile) => {
        if (!active) return
        setForm(toForm(profile))
        setSaved(toForm(profile))
        setLoad({ status: 'ready', error: null })
      })
      .catch((error) => active && setLoad({ status: 'error', error }))
    return () => {
      active = false
    }
  }, [reloadKey])

  if (load.status === 'loading') return <Spinner label="Se încarcă setările…" />
  if (load.status === 'error') {
    return (
      <ErrorState
        title="Nu am putut încărca setările."
        message={errorMessage(load.error)}
        onRetry={() => setReloadKey((key) => key + 1)}
      />
    )
  }

  const update = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }))
    setErrors((current) => ({ ...current, [field]: undefined }))
    setConfirmation(false)
  }

  const setIntensity = (activity, intensity) => {
    const next = { ...form.activities }
    if (intensity) next[activity] = intensity
    else delete next[activity]
    update('activities', next)
  }

  const toggleStyle = (style) =>
    update('styles', form.styles.includes(style) ? form.styles.filter((s) => s !== style) : [...form.styles, style])

  const hasActivity = Object.keys(form.activities).length > 0
  // Bugetul e doar un filtru: fără nicio preferință, recomandările vin din rezervă (cele mai cumpărate).
  const hasPreferences = hasActivity || Boolean(form.level) || form.styles.length > 0 || Boolean(form.season)
  const dirty = sameSettingsKey(form) !== sameSettingsKey(saved)

  async function handleSubmit(event) {
    event.preventDefault()
    const clientErrors = validate(form)
    setErrors(clientErrors)
    setFormError('')
    setConfirmation(false)
    if (Object.keys(clientErrors).length) return

    setSaving(true)
    try {
      const profile = await api.put('/profile', toPayload(form))
      setForm(toForm(profile))
      setSaved(toForm(profile))
      setConfirmation(true)
      notifyUserDataChanged() // recomandările se reîncarcă cu noile setări
    } catch (error) {
      setErrors(profileFieldErrors(error))
      setFormError(errorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  const intensities = [{ value: '', label: 'Deloc' }, ...options('intensities')]

  return (
    <section className="mx-auto max-w-3xl">
      {newAccount && (
        <div className="mb-6 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          Bun venit, <span className="font-semibold">{user?.display_name}</span>! Contul a fost creat. Completează
          setările de profil ca să primești recomandări personalizate.
        </div>
      )}

      <h1 className="text-2xl font-semibold text-gray-900">Setări profil</h1>
      <p className="mt-1 text-sm text-gray-600">
        Recomandările pornesc de la aceste preferințe. Le poți schimba oricând.
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-6 space-y-5">
        <FormError>{formError}</FormError>

        <Section
          title="Activități preferate"
          description="Alege cât de mult practici fiecare activitate. Activitățile contează cel mai mult în recomandări."
          error={errors.activities}
        >
          <div className="space-y-3">
            {options('activities').map((activity) => (
              <div
                key={activity.value}
                className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
                role="radiogroup"
                aria-label={activity.label}
              >
                <span className="text-sm font-medium text-gray-800">{activity.label}</span>
                <div className="flex gap-2">
                  {intensities.map((intensity) => (
                    <Choice
                      key={intensity.value || 'none'}
                      selected={(form.activities[activity.value] ?? '') === intensity.value}
                      onClick={() => setIntensity(activity.value, intensity.value)}
                    >
                      {intensity.label}
                    </Choice>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Nivel de experiență" error={errors.level}>
          <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Nivel de experiență">
            {options('levels').map((level) => (
              <Choice
                key={level.value}
                selected={form.level === level.value}
                onClick={() => update('level', form.level === level.value ? '' : level.value)}
              >
                {level.label}
              </Choice>
            ))}
          </div>
        </Section>

        <Section title="Stil de echipament" description="Poți alege mai multe." error={errors.styles}>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Stil de echipament">
            {options('styles').map((style) => (
              <Choice
                key={style.value}
                type="checkbox"
                selected={form.styles.includes(style.value)}
                onClick={() => toggleStyle(style.value)}
              >
                {style.label}
              </Choice>
            ))}
          </div>
        </Section>

        <Section title="Sezon" error={errors.season}>
          <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Sezon">
            {options('seasons').map((season) => (
              <Choice
                key={season.value}
                selected={form.season === season.value}
                onClick={() => update('season', form.season === season.value ? '' : season.value)}
              >
                {season.label}
              </Choice>
            ))}
          </div>
        </Section>

        <Section
          title="Buget maxim per produs"
          description="Produsele mai scumpe nu apar în recomandări. Lasă gol pentru fără limită."
        >
          <label htmlFor="max_budget" className="sr-only">
            Buget maxim în RON
          </label>
          <div className="flex items-center gap-2">
            <input
              id="max_budget"
              type="number"
              min="1"
              step="10"
              inputMode="decimal"
              value={form.max_budget}
              onChange={(event) => update('max_budget', event.target.value)}
              placeholder="fără limită"
              aria-invalid={Boolean(errors.max_budget)}
              aria-describedby={errors.max_budget ? 'max_budget-error' : undefined}
              className={`block w-40 rounded-md border px-3 py-2 text-sm shadow-sm outline-none focus:ring-2 ${
                errors.max_budget
                  ? 'border-red-400 focus:border-red-500 focus:ring-red-200'
                  : 'border-gray-300 focus:border-emerald-600 focus:ring-emerald-200'
              }`}
            />
            <span className="text-sm text-gray-600">RON</span>
          </div>
          {errors.max_budget && (
            <p id="max_budget-error" className="mt-2 text-sm text-red-600">
              {errors.max_budget}
            </p>
          )}
        </Section>

        {/* Bara de salvare rămâne vizibilă la derulare, util mai ales pe telefon. */}
        <div className="sticky bottom-0 -mx-4 border-t border-gray-200 bg-gray-50/95 px-4 py-4 backdrop-blur sm:mx-0 sm:rounded-xl sm:border sm:bg-white sm:shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div aria-live="polite" className="text-sm">
              {confirmation ? (
                <span className="font-medium text-emerald-800">
                  ✓ Setările au fost salvate.{' '}
                  <Link to="/recomandari" className="underline hover:text-emerald-950">
                    Vezi recomandările
                  </Link>
                </span>
              ) : dirty ? (
                <span className="text-amber-700">Ai modificări nesalvate.</span>
              ) : !hasPreferences ? (
                <span className="text-gray-600">Completează setările ca să primești recomandări personalizate.</span>
              ) : !hasActivity ? (
                <span className="text-gray-600">Alege și o activitate: recomandările vor fi mult mai precise.</span>
              ) : (
                <span className="text-gray-500">Setările sunt la zi.</span>
              )}
            </div>
            <div className="flex gap-2">
              {!dirty && hasPreferences && !confirmation && (
                <Link
                  to="/recomandari"
                  className="rounded-md border border-gray-300 px-4 py-2.5 text-center text-sm font-medium text-gray-700 hover:border-emerald-600 hover:text-emerald-800"
                >
                  Recomandări
                </Link>
              )}
              <button
                type="submit"
                disabled={saving || !dirty}
                className="flex-1 rounded-md bg-emerald-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:cursor-not-allowed disabled:opacity-50 sm:flex-none"
              >
                {saving ? 'Se salvează…' : 'Salvează setările'}
              </button>
            </div>
          </div>
        </div>
      </form>
    </section>
  )
}
