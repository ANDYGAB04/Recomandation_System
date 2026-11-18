import { useEffect, useState } from 'react'
import { getHealth } from '../lib/api.js'

const STATES = {
  checking: { dot: 'bg-gray-400', text: 'Verific API…' },
  ok: { dot: 'bg-emerald-500', text: 'API conectat' },
  error: { dot: 'bg-red-500', text: 'API indisponibil' },
}


export default function ApiStatus() {
  const [status, setStatus] = useState('checking')

  useEffect(() => {
    let active = true
    getHealth()
      .then((data) => active && setStatus(data?.status === 'ok' ? 'ok' : 'error'))
      .catch(() => active && setStatus('error'))
    return () => {
      active = false
    }
  }, [])

  const { dot, text } = STATES[status]
  return (
    <span className="inline-flex items-center gap-2 text-xs text-gray-600" title="GET /health">
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      {text}
    </span>
  )
}
