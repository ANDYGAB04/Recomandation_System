

export function ErrorState({ title = 'Nu am putut încărca datele.', message, onRetry }) {
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-6 text-center">
      <p className="font-medium text-red-800">{title}</p>
      {message && <p className="mt-1 text-sm text-red-700">{message}</p>}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-md bg-white px-4 py-2 text-sm font-medium text-red-700 shadow-sm ring-1 ring-red-200 hover:bg-red-100"
        >
          Încearcă din nou
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, message, action }) {
  return (
    <div className="rounded-lg border border-dashed border-gray-300 bg-white px-4 py-10 text-center">
      <p className="font-medium text-gray-900">{title}</p>
      {message && <p className="mt-1 text-sm text-gray-600">{message}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function TestDataBadge({ className = '' }) {
  return (
    <span
      className={`inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 ${className}`}
      title="Produs fictiv, creat pentru demonstrație"
    >
      Date de test
    </span>
  )
}

export function AvailabilityBadge({ available }) {
  return available ? (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700">
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
      În stoc
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-gray-500">
      <span className="h-1.5 w-1.5 rounded-full bg-gray-400" />
      Indisponibil
    </span>
  )
}
