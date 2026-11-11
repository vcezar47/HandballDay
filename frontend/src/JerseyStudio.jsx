import { useEffect, useState } from 'react'
import { getClubs, getJerseyCatalog, uploadLogo } from './api.js'
import Jersey from './Jersey.jsx'
import Status from './Status.jsx'
import useFetch from './useFetch.js'

const MAX_BYTES = 12 * 1024 * 1024 // same limits as the server, checked here only to save a round trip
const ALLOWED = /\.(png|jpe?g|webp)$/i
const NAME_JUNK = /[^\p{L} .'-]/gu // anything the server would refuse

// Designs a jersey with a live preview. Reports the checkout payload (or null while it is not valid) through onChange.
export default function JerseyStudio({ homeSlug, onChange }) {
  const { data: catalog, error } = useFetch(getJerseyCatalog, [])
  const { data: clubs } = useFetch(getClubs, [])
  const [club, setClub] = useState(homeSlug)
  const [colours, setColours] = useState(null) // { primary, secondary }; null = follow the club
  const [templateId, setTemplateId] = useState(null)
  const [name, setName] = useState('')
  const [number, setNumber] = useState('10')
  const [size, setSize] = useState('M')
  const [logo, setLogo] = useState(null) // { id, preview }
  const [logoError, setLogoError] = useState('')
  const [uploading, setUploading] = useState(false)

  const clubRow = clubs?.find((c) => c.slug === club)
  const primary = colours?.primary ?? clubRow?.primary_color ?? '#014698'
  const secondary = colours?.secondary ?? clubRow?.secondary_color ?? '#ffffff'
  const template = catalog?.templates.find((t) => t.id === templateId) ?? catalog?.templates[0]
  const cleanName = name.trim().toUpperCase()
  const valid = Boolean(template && cleanName && number !== '' && !uploading)

  useEffect(() => {
    onChange(
      valid
        ? {
            club,
            template_id: template.id,
            primary_color: primary,
            secondary_color: secondary,
            name_text: cleanName,
            number: Number(number),
            size,
            logo_upload_id: logo?.id ?? null,
          }
        : null,
      catalog?.price_bani ?? 0,
    )
  }, [valid, club, template, primary, secondary, cleanName, number, size, logo, catalog, onChange])

  useEffect(() => () => logo && URL.revokeObjectURL(logo.preview), [logo])

  async function handleFile(e) {
    const file = e.target.files[0]
    e.target.value = '' // lets the same file be chosen again
    if (!file) return
    setLogoError('')
    if (!ALLOWED.test(file.name)) return setLogoError('Use a PNG, JPG or WebP image')
    if (file.size > MAX_BYTES) return setLogoError('The file is larger than 12 MB')
    setUploading(true)
    try {
      const { id } = await uploadLogo(file)
      setLogo({ id, preview: URL.createObjectURL(file) })
    } catch (err) {
      setLogoError(err.message)
    } finally {
      setUploading(false)
    }
  }

  if (error) return <p className="message error">{error}</p>
  if (!catalog || !clubs) return <Status loading />

  return (
    <fieldset className="studio">
      <legend>Your jersey</legend>
      <div className="jersey-preview">
        <Jersey
          template={template.svg_key}
          primary={primary}
          secondary={secondary}
          name={cleanName}
          number={number}
          logoUrl={logo?.preview}
          label={`Preview of your jersey: ${cleanName || 'no name yet'} number ${number}`}
        />
      </div>
      <div className="studio-fields">
        <label>
          Club
          <select
            value={club}
            onChange={(e) => {
              setClub(e.target.value)
              setColours(null) // back to the new club's colours
            }}
          >
            {clubs.map((c) => (
              <option key={c.slug} value={c.slug}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Style
          <select value={template.id} onChange={(e) => setTemplateId(Number(e.target.value))}>
            {catalog.templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        <div className="colour-row">
          <label>
            Main colour
            <input type="color" value={primary} onChange={(e) => setColours({ primary: e.target.value, secondary })} />
          </label>
          <label>
            Trim colour
            <input type="color" value={secondary} onChange={(e) => setColours({ primary, secondary: e.target.value })} />
          </label>
        </div>
        <label>
          Name on the back
          <input
            value={name}
            onChange={(e) => setName(e.target.value.replace(NAME_JUNK, ''))}
            maxLength={15}
            placeholder="e.g. POPESCU"
            autoComplete="off"
          />
        </label>
        <div className="colour-row">
          <label>
            Number
            <input type="number" min="0" max="99" step="1" value={number} onChange={(e) => setNumber(e.target.value)} />
          </label>
          <label>
            Size
            <select value={size} onChange={(e) => setSize(e.target.value)}>
              {catalog.sizes.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
        </div>
        <label>
          Logo (optional)
          <input type="file" accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp" onChange={handleFile} disabled={uploading} />
        </label>
        {uploading && <p className="muted small">Uploading...</p>}
        {logo && (
          <button type="button" className="link-btn" onClick={() => setLogo(null)}>
            Remove logo
          </button>
        )}
        {logoError && <p className="message error" role="alert">{logoError}</p>}
        <p className="muted small">Up to 12 MB. Your logo is re-encoded and resized on our server.</p>
      </div>
    </fieldset>
  )
}
