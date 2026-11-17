import { useState } from 'react'
import { formatPrice } from './format.js'

// Where each stand sits around the court, in the SVG's own units. Sectors share their side equally.
const BOX = {
  north: { x: 250, y: 108, w: 300, h: 72 },
  south: { x: 250, y: 360, w: 300, h: 72 },
  west: { x: 158, y: 190, w: 82, h: 160 },
  east: { x: 560, y: 190, w: 82, h: 160 },
}
const COLOURS = { VIP: '#f26b21', 'Main stand': '#2563c9', 'End stand': '#0e8f80' }
const GAP = 6

function place(side, index, count) {
  const b = BOX[side]
  if (side === 'north' || side === 'south') {
    const w = (b.w - GAP * (count - 1)) / count
    return { x: b.x + index * (w + GAP), y: b.y, w, h: b.h }
  }
  const h = (b.h - GAP * (count - 1)) / count
  return { x: b.x, y: b.y + index * (h + GAP), w: b.w, h }
}

const seatsOf = (sector) => sector.rows.reduce((a, b) => a + b, 0)

// Seat picker: the hall seen from above, then the seats of the sector you click.
// `selected` is a list of seat codes ("M2-5-12"); `onToggle(code, zoneId)` is called for each click on a seat.
export default function ArenaMap({ seatMap, zones, selected, onToggle }) {
  const [openCode, setOpenCode] = useState(null)
  const taken = new Set(seatMap.taken)
  const price = Object.fromEntries(zones.map((z) => [z.zone_id, z.price_bani]))
  const onSale = (s) => s.zone_id in price
  const open = seatMap.sectors.find((s) => s.code === openCode)

  if (open) return <SectorSeats sector={open} taken={taken} selected={selected} price={price[open.zone_id]} onBack={() => setOpenCode(null)} onToggle={onToggle} />

  const bySide = {}
  seatMap.sectors.forEach((s) => (bySide[s.side] ??= []).push(s))
  const free = (s) => seatsOf(s) - [...taken].filter((c) => c.startsWith(`${s.code}-`)).length

  return (
    <div className="arena">
      <svg viewBox="130 90 540 360" role="group" aria-label="Seating plan: choose a sector">
        <rect className="arena-floor" x="250" y="190" width="300" height="160" rx="4" />
        <g className="arena-lines" aria-hidden="true">
          <path d="M400 190V350" />
          <circle cx="400" cy="270" r="22" />
          <path d="M250 232A38 38 0 0 1 250 308Z" className="arena-goal" />
          <path d="M550 232A38 38 0 0 0 550 308Z" className="arena-goal" />
        </g>
        <text className="arena-label" x="400" y="214" textAnchor="middle">
          COURT
        </text>
        {Object.entries(bySide).flatMap(([side, list]) =>
          list.map((s, i) => {
            const r = place(side, i, list.length)
            const left = free(s)
            const picked = selected.filter((c) => c.startsWith(`${s.code}-`)).length
            const label = `Sector ${s.code}, ${s.zone}, ${left} free seats${picked ? `, ${picked} selected` : ''}`
            return (
              <g
                key={s.code}
                role="button"
                tabIndex={onSale(s) ? 0 : -1}
                aria-label={label}
                aria-disabled={!onSale(s) || left === 0}
                className={`sector${picked ? ' picked' : ''}${!onSale(s) || left === 0 ? ' off' : ''}`}
                onClick={() => onSale(s) && setOpenCode(s.code)}
                onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSale(s) && (e.preventDefault(), setOpenCode(s.code))}
              >
                <rect x={r.x} y={r.y} width={r.w} height={r.h} rx="6" fill={COLOURS[s.zone] ?? '#4b5b73'} fillOpacity={0.35 + 0.65 * (left / seatsOf(s))} />
                <text x={r.x + r.w / 2} y={r.y + r.h / 2 - 2} textAnchor="middle" className="sector-code">
                  {s.code}
                </text>
                <text x={r.x + r.w / 2} y={r.y + r.h / 2 + 15} textAnchor="middle" className="sector-free">
                  {picked ? `${picked} chosen` : `${left} free`}
                </text>
              </g>
            )
          }),
        )}
      </svg>
      <ul className="legend">
        {zones.map((z) => (
          <li key={z.zone_id}>
            <span className="swatch" style={{ background: COLOURS[z.name] ?? '#4b5b73' }} />
            {z.name} <span className="muted">{formatPrice(z.price_bani)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function SectorSeats({ sector, taken, selected, price, onBack, onToggle }) {
  const chosen = new Set(selected)
  return (
    <div className="sector-view">
      <div className="sector-head">
        <button type="button" className="ghost small" onClick={onBack}>
          &larr; All sectors
        </button>
        <h3>
          Sector {sector.code} <span className="muted">&middot; {sector.zone} &middot; {formatPrice(price)} a seat</span>
        </h3>
      </div>
      <div className="seat-scroll">
        <p className="court-side">Court side &uarr;</p>
        {sector.rows.map((length, r) => (
          <div className="seat-row" key={r} role="group" aria-label={`Row ${r + 1}`}>
            <span className="row-no" aria-hidden="true">
              {r + 1}
            </span>
            {Array.from({ length }, (_, n) => {
              const code = `${sector.code}-${r + 1}-${n + 1}`
              const isTaken = taken.has(code)
              const isChosen = chosen.has(code)
              return (
                <button
                  key={code}
                  type="button"
                  className={isChosen ? 'seat chosen' : 'seat'}
                  disabled={isTaken}
                  aria-pressed={isChosen}
                  aria-label={`Row ${r + 1}, seat ${n + 1}${isTaken ? ', taken' : ''}`}
                  title={isTaken ? 'Taken' : `Row ${r + 1}, seat ${n + 1}`}
                  onClick={() => onToggle(code, sector.zone_id)}
                >
                  {n + 1}
                </button>
              )
            })}
          </div>
        ))}
      </div>
      <p className="muted small">Grey seats are taken. Click a seat to choose it, click again to let it go.</p>
    </div>
  )
}
