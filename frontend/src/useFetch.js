import { useEffect, useState } from 'react'

// Runs `load()` again whenever `deps` change. Returns { data } or { error }, or {} while loading.
export default function useFetch(load, deps) {
  const [state, setState] = useState({})

  useEffect(() => {
    let stale = false // a slower, older request must not overwrite a newer one
    setState({})
    load()
      .then((data) => !stale && setState({ data }))
      .catch((err) => !stale && setState({ error: err.message }))
    return () => {
      stale = true
    }
    // `load` is a new closure on every render; `deps` says what it really depends on.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return state
}
