
import { useEffect, useState } from 'react'

const EVENT = 'hobbyshop:user-data-changed'

export function notifyUserDataChanged() {
  window.dispatchEvent(new Event(EVENT))
}

export function useUserDataVersion() {
  const [version, setVersion] = useState(0)
  useEffect(() => {
    const onChange = () => setVersion((v) => v + 1)
    window.addEventListener(EVENT, onChange)
    return () => window.removeEventListener(EVENT, onChange)
  }, [])
  return version
}
