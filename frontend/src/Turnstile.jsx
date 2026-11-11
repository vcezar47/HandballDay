import { useEffect, useRef, useState } from 'react'

const SRC = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
let loading // one script tag for the whole app

function loadScript() {
  loading ??= new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = SRC
    script.async = true
    script.onload = resolve
    script.onerror = () => {
      loading = undefined // allow another try
      reject(new Error('load failed'))
    }
    document.head.append(script)
  })
  return loading
}

// Cloudflare Turnstile widget. Calls onToken(token) when the visitor passes and onToken('') when the token
// expires or fails. A token works once: after using it, remount this component (change its `key`) to get a new one.
export default function Turnstile({ siteKey, onToken }) {
  const box = useRef(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let widget
    let gone = false
    loadScript()
      .then(() => {
        if (gone) return
        widget = window.turnstile.render(box.current, {
          sitekey: siteKey,
          callback: onToken,
          'expired-callback': () => onToken(''),
          'error-callback': () => onToken(''),
        })
      })
      .catch(() => !gone && setFailed(true))
    return () => {
      gone = true
      if (widget !== undefined) window.turnstile.remove(widget)
    }
  }, [siteKey, onToken])

  return (
    <>
      <div ref={box} className="turnstile" />
      {failed && <p className="message error" role="alert">The CAPTCHA could not be loaded. Check your connection and reload the page.</p>}
    </>
  )
}
