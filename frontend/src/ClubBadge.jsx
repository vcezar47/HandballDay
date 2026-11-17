import { useState } from 'react'

export function textColour(hex) {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16))
  return 0.299 * r + 0.587 * g + 0.114 * b > 150 ? '#111' : '#fff'
}

// The club's crest (public/crests/<slug>.webp) on a white disc, so every crest reads on any colour.
// If the image is missing, falls back to club colours and the city's initials.
export default function ClubBadge({ club, size = 40 }) {
  const [broken, setBroken] = useState(false)

  if (!broken && club.slug) {
    return (
      <img
        className="badge crest"
        src={`/crests/${club.slug}.webp`}
        width={size}
        height={size}
        style={{ padding: Math.round(size * 0.14) }} // percentages would resolve against the parent, not the image
        alt={`${club.name} badge`}
        onError={() => setBroken(true)}
      />
    )
  }

  const initials = club.city
    .split(/[\s-]+/)
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
  return (
    <svg className="badge" width={size} height={size} viewBox="0 0 48 48" role="img" aria-label={`${club.name} badge`}>
      <circle cx="24" cy="24" r="22" fill={club.primary_color} stroke={club.secondary_color} strokeWidth="3" />
      <text x="24" y="30" textAnchor="middle" fontSize="17" fontWeight="700" fill={textColour(club.primary_color)}>
        {initials}
      </text>
    </svg>
  )
}
