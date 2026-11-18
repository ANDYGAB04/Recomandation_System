import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { FormError } from '../components/Form.jsx'
import Spinner from '../components/Spinner.jsx'
import { ErrorState } from '../components/Status.jsx'
import { ApiError, api, errorMessage } from '../lib/api.js'

const SCALE = [1, 2, 3, 4, 5]


function questionErrors(error) {
  if (!(error instanceof ApiError) || error.status !== 422 || !Array.isArray(error.data?.detail)) return {}
  const errors = {}
  for (const item of error.data.detail) {
    const id = item.loc?.[item.loc.length - 1]
    if (typeof id === 'string' && !errors[id]) errors[id] = item.msg.replace(/^Value error, /, '')
  }
  return errors
}


export default function SurveyPage() {
  const [load, setLoad] = useState({ status: 'loading', data: null, error: null })
  const [reloadKey, setReloadKey] = useState(0)
  const [answers, setAnswers] = useState({})
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [sending, setSending] = useState(false)
  const [done, setDone] = useState(false)
  const busy = useRef(false)

  useEffect(() => {
    let active = true
    setLoad((current) => ({ ...current, status: 'loading', error: null }))
    api
      .get('/survey')
      .then((data) => active && setLoad({ status: 'ready', data, error: null }))
      .catch((error) => active && setLoad({ status: 'error', data: null, error }))
    return () => {
      active = false
    }
  }, [reloadKey])

  if (load.status === 'error') {
    return <ErrorState title="Nu am putut încărca chestionarul." message={errorMessage(load.error)} onRetry={() => setReloadKey((k) => k + 1)} />
  }
  if (!load.data) return <Spinner label="Se încarcă chestionarul…" />

  if (done || load.data.answered) {
    return (
      <section className="mx-auto max-w-2xl rounded-xl border border-emerald-200 bg-emerald-50 p-6 text-center sm:p-8">
        <h1 className="text-2xl font-semibold text-emerald-900">Mulțumim!</h1>
        <p className="mt-2 text-sm text-emerald-900">
          {done ? 'Răspunsurile tale au fost salvate.' : 'Ai completat deja chestionarul.'} Ne ajută să evaluăm cât de utile
          sunt recomandările.
        </p>
        <Link to="/recomandari" className="mt-5 inline-block rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800">
          Înapoi la recomandări
        </Link>
      </section>
    )
  }

  const { questions } = load.data
  const set = (id, value) => {
    setAnswers((current) => ({ ...current, [id]: value }))
    setErrors((current) => ({ ...current, [id]: undefined }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (busy.current) return
    const missing = {}
    for (const q of questions) if (q.kind === 'scale' && answers[q.id] == null) missing[q.id] = 'Alege un răspuns.'
    setErrors(missing)
    setFormError(Object.keys(missing).length ? 'Răspunde la toate întrebările cu scală (ultima e opțională).' : '')
    if (Object.keys(missing).length) {
      document.getElementById(`intrebare-${Object.keys(missing)[0]}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      return
    }

    busy.current = true
    setSending(true)
    try {
      await api.post('/survey', { answers })
      setDone(true)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (error) {
      if (error.status === 409) {
        setDone(true)
        return
      }
      setErrors(questionErrors(error))
      setFormError(errorMessage(error))
    } finally {
      busy.current = false
      setSending(false)
    }
  }

  const answeredCount = questions.filter((q) => q.kind === 'scale' && answers[q.id] != null).length
  const scaleCount = questions.filter((q) => q.kind === 'scale').length

  return (
    <section className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-semibold text-gray-900">Chestionar: cât de utile sunt recomandările?</h1>
      <p className="mt-2 text-sm text-gray-600">
        Durează aproximativ 2 minute. Răspunsurile sunt <span className="font-medium">anonime</span>: nu se salvează
        numele, e-mailul sau contul tău, doar faptul că ai răspuns, ca să nu completezi de două ori.
      </p>
      <p className="mt-2 text-sm text-gray-600">
        Înainte să răspunzi, completează{' '}
        <Link to="/setari" className="font-medium text-emerald-700 underline hover:text-emerald-900">
          setările
        </Link>
        , uită-te la{' '}
        <Link to="/recomandari" className="font-medium text-emerald-700 underline hover:text-emerald-900">
          recomandări
        </Link>{' '}
        și schimbă cel puțin o setare, ca să vezi cum se schimbă lista.
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-6 space-y-4">
        <FormError>{formError}</FormError>

        {questions.map((q, index) => (
          <fieldset
            key={q.id}
            id={`intrebare-${q.id}`}
            className={`rounded-xl border bg-white p-5 shadow-sm ${errors[q.id] ? 'border-red-300' : 'border-gray-200'}`}
          >
            <legend className="sr-only">{q.text}</legend>
            <p className="font-medium text-gray-900" aria-hidden="true">
              <span className="mr-2 text-gray-400">{index + 1}.</span>
              {q.text}
              {q.kind === 'open' && <span className="ml-1 text-sm font-normal text-gray-500">(opțional)</span>}
            </p>

            {q.kind === 'scale' ? (
              <div className="mt-4">
                <div className="grid grid-cols-5 gap-2" role="radiogroup" aria-label={q.text}>
                  {SCALE.map((value) => {
                    const selected = answers[q.id] === value
                    return (
                      <button
                        key={value}
                        type="button"
                        role="radio"
                        aria-checked={selected}
                        aria-label={`${value}${value === 1 ? ` – ${q.low}` : value === 5 ? ` – ${q.high}` : ''}`}
                        onClick={() => set(q.id, value)}
                        className={`rounded-lg border py-2.5 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-emerald-300 ${
                          selected
                            ? 'border-emerald-700 bg-emerald-700 text-white'
                            : 'border-gray-300 bg-white text-gray-700 hover:border-emerald-600 hover:text-emerald-800'
                        }`}
                      >
                        {value}
                      </button>
                    )
                  })}
                </div>
                <div className="mt-1 flex justify-between text-xs text-gray-500">
                  <span>1 = {q.low}</span>
                  <span>5 = {q.high}</span>
                </div>
              </div>
            ) : (
              <textarea
                rows={4}
                maxLength={1000}
                value={answers[q.id] ?? ''}
                onChange={(event) => set(q.id, event.target.value)}
                aria-label={q.text}
                placeholder="Scrie aici, dacă vrei."
                className="mt-3 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-200"
              />
            )}

            {errors[q.id] && (
              <p role="alert" className="mt-2 text-sm text-red-600">
                {errors[q.id]}
              </p>
            )}
          </fieldset>
        ))}

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-gray-500">
            {answeredCount} din {scaleCount} întrebări cu scală
          </p>
          <button
            type="submit"
            disabled={sending}
            className="rounded-md bg-emerald-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {sending ? 'Se trimite…' : 'Trimite răspunsurile'}
          </button>
        </div>
      </form>
    </section>
  )
}
