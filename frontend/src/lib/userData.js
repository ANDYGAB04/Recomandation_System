/**
 * Anunță paginile că datele utilizatorului s-au schimbat (setări salvate, favorit, cumpărare),
 * ca listele care depind de ele (recomandările, produsele similare) să se reîncarce singure.
 *
 *   notifyUserDataChanged()            // după PUT /profile sau POST /interactions reușit
 *   const version = useUserDataVersion() // folosit ca dependență într-un useEffect
 */
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
