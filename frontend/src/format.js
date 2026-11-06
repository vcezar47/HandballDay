// All times are shown in the clubs' own timezone, whatever the visitor's.
const TZ = 'Europe/Bucharest'
const date = new Intl.DateTimeFormat('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', timeZone: TZ })
const time = new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: TZ })
const money = new Intl.NumberFormat('ro-RO', { style: 'currency', currency: 'RON' })

export const formatDate = (iso) => date.format(new Date(iso))
export const formatTime = (iso) => time.format(new Date(iso))
export const formatPrice = (bani) => money.format(bani / 100)
