import { Link } from 'react-router'
import ClubBadge, { textColour } from './ClubBadge.jsx'

// One flat block per club, in its own colour; used on the home page and the club list.
export default function ClubBlocks({ clubs }) {
  return (
    <ul className="club-blocks">
      {clubs.map((c) => (
        <li key={c.slug}>
          <Link to={`/clubs/${c.slug}`} style={{ '--c': c.primary_color, '--t': textColour(c.primary_color) }}>
            <ClubBadge club={c} size={44} />
            {c.name}
          </Link>
        </li>
      ))}
    </ul>
  )
}
