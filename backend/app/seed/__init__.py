"""Demo data: roles, the 14 Liga Florilor 2026/27 clubs, a generated fixture list and ticket zones.

Idempotent: every step skips what already exists. Run with `python -m app.seed`.
The fixtures and prices are invented demo data; the clubs come from clubs.json.
"""

import json
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Club, Fixture, FixtureZone, JerseyTemplate, League, Role, Venue, Zone
from ..repositories import ClubRepository

CLUBS_FILE = Path(__file__).with_name("clubs.json")
ROLES = ("fan", "staff", "admin")
# (name, svg_key): the key picks the drawing in frontend/src/Jersey.jsx
TEMPLATES = (("Classic", "classic"), ("Stripes", "stripes"), ("Sash", "sash"))
# (zone name, share of the venue capacity in %, price in bani); the last zone takes the remainder.
ZONES = (("VIP", 20, 8000), ("Main stand", 50, 4500), ("End stand", 30, 2500))


def ensure_roles(db: Session) -> None:
    have = set(db.scalars(select(Role.name)))
    db.add_all(Role(name=n) for n in ROLES if n not in have)
    db.commit()


def round_robin(ids: list[int]) -> list[list[tuple[int, int]]]:
    """Double round robin (circle method): n-1 rounds, then the same rounds with sides swapped."""
    n = len(ids)
    ring, first_half = list(ids), []
    for _ in range(n - 1):
        first_half.append([(ring[i], ring[n - 1 - i]) for i in range(n // 2)])
        ring = [ring[0], ring[-1], *ring[1:-1]]
    # Alternate home/away by round so a club is not always at home against the same opponent order.
    first_half = [[(a, b) if (r + i) % 2 == 0 else (b, a) for i, (a, b) in enumerate(rnd)]
                  for r, rnd in enumerate(first_half)]
    return first_half + [[(b, a) for a, b in rnd] for rnd in first_half]


def seed_clubs(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Club)):
        return
    league = League(name="Liga Florilor 2026/27", country="Romania")
    db.add(league)
    db.flush()
    for c in json.loads(CLUBS_FILE.read_text(encoding="utf-8")):
        venue = Venue(name=c["venue"], city=c["city"])
        db.add(venue)
        db.flush()
        db.add(Club(
            league_id=league.id, venue_id=venue.id, name=c["name"], slug=c["slug"], city=c["city"],
            founded_year=c["founded_year"], description=c["description"],
            primary_color=c["primary_color"], secondary_color=c["secondary_color"],
        ))
        left = c["capacity"]
        for i, (name, share, _) in enumerate(ZONES):
            cap = left if i == len(ZONES) - 1 else c["capacity"] * share // 100
            left -= cap
            db.add(Zone(venue_id=venue.id, name=name, capacity=cap))
    db.commit()


def seed_fixtures(db: Session, now: datetime | None = None) -> None:
    if db.scalar(select(func.count()).select_from(Fixture)):
        return
    clubs = sorted(ClubRepository(db).list(), key=lambda c: c.id)
    by_id = {c.id: c for c in clubs}
    zones = defaultdict(list)
    for z in db.scalars(select(Zone).order_by(Zone.id)):
        zones[z.venue_id].append(z)

    now = now or datetime.now(timezone.utc)
    days_to_saturday = (5 - now.weekday()) % 7 or 7
    first_saturday = datetime.combine((now + timedelta(days=days_to_saturday)).date(), time(16), timezone.utc)

    for r, rnd in enumerate(round_robin(list(by_id))):
        for home, away in rnd:
            venue_id = by_id[home].venue_id
            fixture = Fixture(
                home_club_id=home, away_club_id=away, venue_id=venue_id,
                kickoff_at=first_saturday + timedelta(weeks=r),
            )
            db.add(fixture)
            db.flush()
            for zone, (_, _, price) in zip(zones[venue_id], ZONES):
                db.add(FixtureZone(fixture_id=fixture.id, zone_id=zone.id, price_bani=price, quota=zone.capacity))
    db.commit()


def seed_templates(db: Session) -> None:
    have = set(db.scalars(select(JerseyTemplate.name)))
    db.add_all(JerseyTemplate(name=n, svg_key=k) for n, k in TEMPLATES if n not in have)
    db.commit()


def seed_all(db: Session) -> None:
    ensure_roles(db)
    seed_templates(db)
    seed_clubs(db)
    seed_fixtures(db)
