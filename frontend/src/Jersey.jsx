import { useId } from 'react'
import { textColour } from './ClubBadge.jsx'

const BODY =
  'M70 10 L40 22 L8 70 L36 92 L52 74 L52 205 Q52 212 60 212 L140 212 Q148 212 148 205 L148 74 L164 92 L192 70 L160 22 L130 10 Q100 30 70 10 Z'

// Back view of a jersey. The colours are CSS variables on the <svg>, so changing them recolours the
// whole drawing (and the CSS transition on `fill` animates it). Text is drawn by React, never as markup.
export default function Jersey({ template = 'classic', primary, secondary, name = '', number = '', logoUrl, label }) {
  const clip = useId()
  const ink = textColour(primary)
  const outline = ink === '#fff' ? '#111' : '#fff' // keeps the print readable on any template colours

  return (
    <svg
      className="jersey"
      viewBox="0 0 200 222"
      role="img"
      aria-label={label || `Jersey ${name} ${number}`}
      style={{ '--primary': primary, '--secondary': secondary }}
    >
      <defs>
        <clipPath id={clip}>
          <path d={BODY} />
        </clipPath>
      </defs>
      <path className="j-primary" d={BODY} />
      <g clipPath={`url(#${clip})`}>
        {template === 'stripes' &&
          [0, 1, 2, 3].map((i) => <rect key={i} className="j-secondary" x={36 + i * 40} y="0" width="20" height="222" />)}
        {template === 'sash' && <polygon className="j-secondary" points="0,60 60,60 200,170 200,222 150,222 0,100" />}
        {/* cuffs and collar, on every template */}
        <path className="j-secondary" d="M0 66 L40 96 L30 112 L-10 82 Z M200 66 L160 96 L170 112 L210 82 Z" />
      </g>
      <path className="j-secondary" d="M70 10 Q100 30 130 10 L124 6 Q100 20 76 6 Z" />
      <path d={BODY} fill="none" stroke="rgb(0 0 0 / 0.35)" strokeWidth="1.5" />
      <g textAnchor="middle" fill={ink} stroke={outline} strokeWidth="3" paintOrder="stroke" fontWeight="800">
        <text x="100" y="66" fontSize="17" letterSpacing="1">
          {name}
        </text>
        <text x="100" y="140" fontSize="72">
          {number}
        </text>
      </g>
      {logoUrl && <image href={logoUrl} x="76" y="156" width="48" height="42" preserveAspectRatio="xMidYMid meet" />}
    </svg>
  )
}
