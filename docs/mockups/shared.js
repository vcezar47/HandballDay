// Shared data and helpers for the home page mockups (static demo, no backend).
const SHORT = ['Minaur', 'Corona', 'Craiova', 'CSM', 'Iași', 'Mureș', 'Știința', 'Dunărea', 'Gloria', 'Vâlcea', 'Rapid', 'Slatina', 'Jiu', 'Zalău']
const CLUBS = [
  ['Minaur Baia Mare', 'Baia Mare', '#014698', '#ffffff'],
  ['CSM Corona Brașov', 'Brașov', '#124495', '#e9e173'],
  ['SCM Universitatea Craiova', 'Craiova', '#007aaf', '#5d4c45'],
  ['CSM București', 'București', '#303e87', '#ffffff'],
  ['CSM Iași 2020', 'Iași', '#bd1f23', '#000000'],
  ['CSM Târgu Mureș', 'Târgu Mureș', '#194280', '#c41230'],
  ['CSU Știința București', 'București', '#fceb0c', '#050708'],
  ['Dunărea Brăila', 'Brăila', '#2c457a', '#f0f1f4'],
  ['Gloria Bistrița', 'Bistrița', '#d7041e', '#010101'],
  ['SCM Râmnicu Vâlcea', 'Râmnicu Vâlcea', '#033265', '#bb0606'],
  ['Rapid București', 'București', '#91232b', '#ffffff'],
  ['CSM Slatina', 'Slatina', '#2888b9', '#fdfefd'],
  ['CSM Târgu Jiu', 'Târgu Jiu', '#076cd4', '#72818f'],
  ['HC Zalău', 'Zalău', '#005dad', '#fffefe'],
].map(([name, city, primary, secondary], i) => ({ name, city, primary, secondary, short: SHORT[i] }))

const club = (n) => CLUBS.find((c) => c.name === n)
const FIXTURES = [
  ['Rapid București', 'CSU Știința București', 'Sat 21 Nov', '18:00', 'Sala Giulești'],
  ['Gloria Bistrița', 'Minaur Baia Mare', 'Sun 22 Nov', '17:00', 'TeraPlast Arena'],
  ['CSM București', 'SCM Râmnicu Vâlcea', 'Wed 25 Nov', '19:00', 'Sala Polivalentă'],
  ['Dunărea Brăila', 'CSM Iași 2020', 'Sat 28 Nov', '18:00', 'Sala Polivalentă Danubius'],
  ['SCM Universitatea Craiova', 'CSM Slatina', 'Sun 29 Nov', '16:00', 'Sala Polivalentă Craiova'],
].map(([h, a, date, time, venue], i) => ({ id: i + 1, home: club(h), away: club(a), date, time, venue }))

function textColour(hex) {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16))
  return 0.299 * r + 0.587 * g + 0.114 * b > 150 ? '#111' : '#fff'
}

function initials(c) {
  return c.city.split(/[\s-]+/).map((w) => w[0]).join('').slice(0, 2).toUpperCase()
}

// Same stand-in crest as frontend/src/ClubBadge.jsx
function badge(c, size = 48) {
  return `<svg class="badge" width="${size}" height="${size}" viewBox="0 0 48 48" role="img" aria-label="${c.name} badge">
    <circle cx="24" cy="24" r="22" fill="${c.primary}" stroke="${c.secondary}" stroke-width="3"/>
    <text x="24" y="30" text-anchor="middle" font-size="17" font-weight="700" fill="${textColour(c.primary)}" font-family="sans-serif">${initials(c)}</text></svg>`
}

// Simple short-sleeve jersey; colours come from CSS variables so they can transition.
function jersey(c, num = 9, name = 'POPESCU') {
  return `<svg class="jersey" viewBox="0 0 120 124" role="img" aria-label="${c.name} jersey">
    <path class="j-body" d="M38 6 L50 2 Q60 12 70 2 L82 6 L114 30 L100 50 L88 42 L88 118 L32 118 L32 42 L20 50 L6 30 Z" fill="${c.primary}"/>
    <path class="j-trim" d="M38 6 L50 2 Q60 12 70 2 L82 6 L86 9 Q60 26 34 9 Z" fill="${c.secondary}"/>
    <path class="j-trim" d="M6 30 L20 50 L26 46 L12 27 Z M114 30 L100 50 L94 46 L108 27 Z" fill="${c.secondary}"/>
    <text class="j-num" x="60" y="74" text-anchor="middle" font-size="34" font-weight="800" fill="${textColour(c.primary)}">${num}</text>
    <text class="j-name" x="60" y="40" text-anchor="middle" font-size="7.5" font-weight="700" letter-spacing=".5" fill="${textColour(c.primary)}">${name}</text></svg>`
}

// A QR-looking pattern (decorative only).
function qr(seed = 1, size = 96) {
  let s = seed * 9301 + 49297, cells = ''
  const rnd = () => ((s = (s * 9301 + 49297) % 233280) / 233280)
  const N = 21, u = size / N
  const finder = (x, y) => `<rect x="${x * u}" y="${y * u}" width="${7 * u}" height="${7 * u}" fill="currentColor"/><rect x="${(x + 1) * u}" y="${(y + 1) * u}" width="${5 * u}" height="${5 * u}" fill="var(--qr-bg,#fff)"/><rect x="${(x + 2) * u}" y="${(y + 2) * u}" width="${3 * u}" height="${3 * u}" fill="currentColor"/>`
  for (let y = 0; y < N; y++)
    for (let x = 0; x < N; x++) {
      const inFinder = (x < 8 && y < 8) || (x > 12 && y < 8) || (x < 8 && y > 12)
      if (!inFinder && rnd() > 0.52) cells += `<rect x="${x * u}" y="${y * u}" width="${u}" height="${u}" fill="currentColor"/>`
    }
  return `<svg class="qr" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" aria-hidden="true">${cells}${finder(0, 0)}${finder(14, 0)}${finder(0, 14)}</svg>`
}

// Same behaviour as frontend/src/Carousel.jsx: autoplay, pause, arrows, dots, swipe, arrow keys,
// pauses on hover/focus, off under reduced motion. Designs style the .cv-* classes.
function carousel(root, { render, onChange = () => {}, interval = 5000, label = 'Upcoming matches' }) {
  let i = 0, hovered = false, startX = null
  let stopped = matchMedia('(prefers-reduced-motion: reduce)').matches
  const n = FIXTURES.length
  root.classList.add('cv')
  root.setAttribute('aria-roledescription', 'carousel')
  root.setAttribute('aria-label', label)
  root.tabIndex = 0
  root.innerHTML = `<div class="cv-viewport"><div class="cv-track">${FIXTURES.map(
    (f, k) => `<article class="cv-slide" role="group" aria-roledescription="slide" aria-label="${k + 1} of ${n}">${render(f, k)}</article>`).join('')}</div></div>
    <div class="cv-controls">
      <button type="button" class="cv-btn cv-prev" aria-label="Previous match">&lsaquo;</button>
      <div class="cv-dots">${FIXTURES.map((_, k) => `<button type="button" class="cv-dot" aria-label="Go to match ${k + 1}"></button>`).join('')}</div>
      <button type="button" class="cv-btn cv-pause">${stopped ? 'Play' : 'Pause'}</button>
      <button type="button" class="cv-btn cv-next" aria-label="Next match">&rsaquo;</button></div>`
  const track = root.querySelector('.cv-track'), dots = [...root.querySelectorAll('.cv-dot')]
  const slides = [...root.querySelectorAll('.cv-slide')], pause = root.querySelector('.cv-pause')
  const go = (k) => {
    i = (k + n) % n
    track.style.transform = `translateX(-${i * 100}%)`
    dots.forEach((d, j) => { d.classList.toggle('active', j === i); d.setAttribute('aria-current', j === i) })
    slides.forEach((s, j) => (s.inert = j !== i))
    root.dataset.index = i
    onChange(i, FIXTURES[i])
  }
  root.querySelector('.cv-prev').onclick = () => go(i - 1)
  root.querySelector('.cv-next').onclick = () => go(i + 1)
  dots.forEach((d, k) => (d.onclick = () => go(k)))
  pause.onclick = () => { stopped = !stopped; pause.textContent = stopped ? 'Play' : 'Pause'; pause.setAttribute('aria-pressed', stopped) }
  root.onkeydown = (e) => { if (e.key === 'ArrowLeft') go(i - 1); if (e.key === 'ArrowRight') go(i + 1) }
  root.onmouseenter = root.onfocus = () => (hovered = true)
  root.onmouseleave = root.onblur = () => (hovered = false)
  const vp = root.querySelector('.cv-viewport')
  vp.onpointerdown = (e) => (startX = e.clientX)
  vp.onpointerup = (e) => { if (startX !== null && Math.abs(e.clientX - startX) > 40) go(i + (e.clientX < startX ? 1 : -1)); startX = null }
  setInterval(() => { if (!stopped && !hovered) go(i + 1) }, interval)
  go(0)
  return { go }
}

const FOOTER_NOTE = 'Unofficial student project. Payments run in Stripe test mode and no real tickets are sold.'
