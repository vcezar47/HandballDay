// Handball court seen from above (40 x 20 m): goal areas, 9 m free-throw lines, 7 m marks. Decorative only.
export default function Court() {
  return (
    <svg className="court" viewBox="-12 -12 424 224" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <rect x="-12" y="-12" width="424" height="224" fill="#2563c9" />
      <g id="court-half">
        <path d="M0 33A60 60 0 0 1 60 93L60 107A60 60 0 0 1 0 167Z" fill="#f26b21" />
        <path d="M0 3A90 90 0 0 1 90 93L90 107A90 90 0 0 1 0 197" fill="none" stroke="#fff" strokeWidth="2" strokeDasharray="9 6" />
        <path d="M0 33A60 60 0 0 1 60 93L60 107A60 60 0 0 1 0 167" fill="none" stroke="#fff" strokeWidth="2.5" />
        <path d="M70 97V103" stroke="#fff" strokeWidth="2.5" />
        <rect x="-5" y="93" width="5" height="14" fill="#fff" />
      </g>
      <use href="#court-half" transform="translate(400 0) scale(-1 1)" />
      <rect x="0" y="0" width="400" height="200" fill="none" stroke="#fff" strokeWidth="2.5" />
      <path d="M200 0V200" stroke="#fff" strokeWidth="2.5" />
      <circle cx="200" cy="100" r="3" fill="#fff" />
    </svg>
  )
}
