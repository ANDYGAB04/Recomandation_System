import { useFeedbackVote } from '../lib/feedback.js'


export default function FeedbackButtons({ productId, strategy }) {
  const { enabled, loaded, vote, pending, error, send } = useFeedbackVote(productId)
  if (!enabled) return null

  const button = (useful, label) => {
    const selected = vote === useful
    return (
      <button
        type="button"
        aria-pressed={selected}
        disabled={!loaded || pending}
        onClick={() => send(useful, strategy)}
        className={`rounded-md border px-3 py-1 text-xs font-semibold transition focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:cursor-not-allowed disabled:opacity-60 ${
          selected
            ? useful
              ? 'border-emerald-700 bg-emerald-700 text-white'
              : 'border-gray-700 bg-gray-700 text-white'
            : 'border-gray-300 bg-white text-gray-700 hover:border-emerald-600 hover:text-emerald-800'
        }`}
      >
        {label}
      </button>
    )
  }

  return (
    <div className="relative z-10 mt-3 border-t border-gray-100 pt-3">
      <div className="flex items-center justify-between gap-2" role="group" aria-label="Ți-a fost utilă această recomandare?">
        <span className="text-xs text-gray-600">Ți-a fost utilă?</span>
        <div className="flex gap-2">
          {button(true, 'Da')}
          {button(false, 'Nu')}
        </div>
      </div>
      <p aria-live="polite" className="mt-1 min-h-4 text-xs">
        {error ? (
          <span className="text-red-600">{error}</span>
        ) : vote !== undefined && !pending ? (
          <span className="text-gray-500">Mulțumim! Poți schimba răspunsul oricând.</span>
        ) : null}
      </p>
    </div>
  )
}
