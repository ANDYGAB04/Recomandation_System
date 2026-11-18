
import { useEffect, useState } from 'react'
import { api } from './api.js'

let cache = null
let pending = null

function loadVocabulary() {
  if (cache) return Promise.resolve(cache)
  if (!pending) {
    pending = api
      .get('/vocabulary')
      .then((data) => (cache = data))
      .finally(() => {
        pending = null
      })
  }
  return pending
}

export function useVocabulary() {
  const [vocabulary, setVocabulary] = useState(cache)

  useEffect(() => {
    if (vocabulary) return
    let active = true
    loadVocabulary()
      .then((data) => active && setVocabulary(data))
      .catch(() => {}) 
    return () => {
      active = false
    }
  }, [vocabulary])

  const options = (group) => vocabulary?.[group] ?? []
  const label = (group, value) => options(group).find((option) => option.value === value)?.label ?? value
  return { vocabulary, options, label }
}
