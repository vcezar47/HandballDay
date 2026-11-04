from collections import Counter

from sqlalchemy import func, select

from app.models import Club, Fixture, FixtureZone, Role, Zone
from app.seed import ZONES, round_robin, seed_all


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_round_robin_every_pair_plays_twice_once_each_way():
    rounds = round_robin(list(range(14)))
    assert len(rounds) == 26 and all(len(r) == 7 for r in rounds)
    for rnd in rounds:  # nobody plays twice in a round
        assert len({t for match in rnd for t in match}) == 14
    games = Counter(m for rnd in rounds for m in rnd)
    assert len(games) == 14 * 13 and set(games.values()) == {1}


def test_seed_creates_clubs_fixtures_and_zones(db):
    seed_all(db)
    assert count(db, Role) == 3
    assert count(db, Club) == 14
    assert count(db, Fixture) == 182
    assert count(db, FixtureZone) == 182 * len(ZONES)
    for club in db.scalars(select(Club)):
        capacity = db.scalar(select(func.sum(Zone.capacity)).where(Zone.venue_id == club.venue_id))
        assert capacity > 0 and club.primary_color.startswith("#")


def test_seed_is_idempotent(db):
    seed_all(db)
    seed_all(db)
    assert count(db, Club) == 14 and count(db, Fixture) == 182 and count(db, Role) == 3
