import { useEffect } from 'react'
import { useLocation } from 'react-router'

const DEFAULT_DESCRIPTION = 'Handball matchday tickets and custom jerseys for the Romanian Liga Florilor.'

function upsert(selector, tag, attrs) {
  let el = document.head.querySelector(selector)
  if (!el) {
    el = document.createElement(tag)
    document.head.append(el)
  }
  Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v))
}

// Sets the tab title, meta description and canonical URL for the current page. Renders nothing.
export default function Seo({ title, description = DEFAULT_DESCRIPTION }) {
  const { pathname } = useLocation()

  useEffect(() => {
    document.title = title ? `${title} | HandballDay` : 'HandballDay'
    upsert('meta[name="description"]', 'meta', { name: 'description', content: description })
    upsert('link[rel="canonical"]', 'link', { rel: 'canonical', href: window.location.origin + pathname })
  }, [title, description, pathname])

  return null
}
