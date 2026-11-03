import { useEffect, useRef } from 'react'

// Each band is a bundle of thin lines that drift like silk threads.
const BANDS = [
  { hue: 255, y: 0.36, amp: 0.15, speed: 0.00018, lines: 26, spread: 0.11 },
  { hue: 190, y: 0.56, amp: 0.12, speed: 0.00023, lines: 22, spread: 0.09 },
  { hue: 300, y: 0.74, amp: 0.1, speed: 0.00015, lines: 20, spread: 0.08 },
]

const STEP = 10 // horizontal sampling distance in px

export default function FlowBackground() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    let w = 0
    let h = 0
    let raf = 0
    const pointer = { x: 0.5, y: 0.5, tx: 0.5, ty: 0.5 }

    function draw(now) {
      pointer.x += (pointer.tx - pointer.x) * 0.03
      pointer.y += (pointer.ty - pointer.y) * 0.03

      ctx.globalCompositeOperation = 'source-over'
      ctx.fillStyle = '#05050d'
      ctx.fillRect(0, 0, w, h)
      ctx.globalCompositeOperation = 'lighter'
      ctx.lineWidth = 1

      for (const band of BANDS) {
        const t = now * band.speed
        for (let i = 0; i < band.lines; i++) {
          const k = i / (band.lines - 1) - 0.5 // -0.5 .. 0.5 across the band
          ctx.beginPath()
          for (let x = 0; x <= w + STEP; x += STEP) {
            const nx = x / w + (pointer.x - 0.5) * 0.08
            const wave =
              Math.sin(nx * 3.2 + t * 2 + k * 2.4) * 0.5 +
              Math.sin(nx * 6.1 - t * 3 + k * 4 + band.hue) * 0.25
            const y =
              (band.y +
                (pointer.y - 0.5) * 0.06 +
                wave * band.amp +
                k * band.spread * (1 + Math.sin(nx * 2 + t) * 0.6)) *
              h
            if (x === 0) ctx.moveTo(x, y)
            else ctx.lineTo(x, y)
          }
          const alpha = 0.08 + 0.12 * (1 - Math.abs(k) * 2)
          ctx.strokeStyle = `hsla(${band.hue + k * 40}, 85%, 62%, ${alpha})`
          ctx.stroke()
        }
      }
    }

    function loop(now) {
      draw(now)
      raf = requestAnimationFrame(loop)
    }

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      w = window.innerWidth
      h = window.innerHeight
      canvas.width = w * dpr
      canvas.height = h * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      if (reduced) draw(0)
    }

    function onMove(e) {
      pointer.tx = e.clientX / w
      pointer.ty = e.clientY / h
    }

    resize()
    window.addEventListener('resize', resize)
    if (!reduced) {
      window.addEventListener('pointermove', onMove)
      raf = requestAnimationFrame(loop)
    }

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', resize)
      window.removeEventListener('pointermove', onMove)
    }
  }, [])

  return <canvas ref={canvasRef} className="flow" aria-hidden="true" />
}
