
export default function PagePlaceholder({ title, step, children }) {
  return (
    <section>
      <h1 className="text-2xl font-semibold text-gray-900">{title}</h1>
      <div className="mt-4 rounded-lg border border-dashed border-gray-300 bg-white p-6 text-sm text-gray-600">
        {children ?? 'Pagina urmează să fie implementată.'}
        {step && <p className="mt-2 text-xs text-gray-400">Se implementează la {step}.</p>}
      </div>
    </section>
  )
}
