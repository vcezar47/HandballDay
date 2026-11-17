"""Seating plan of a venue, generated from its zones.

Every venue has the same three zones (VIP, Main stand, End stand) with different capacities, so the
plan is drawn from the capacities: VIP on the north side, the Main stand on the south side and the
End stand split between the two ends. Each stand is cut into sectors of roughly the same size, and
each sector into rows. The seats of a zone add up to the zone's capacity exactly.

A seat code is "<sector>-<row>-<number>", for example "M2-5-12": sector M2, row 5 (row 1 is the one
nearest the court), seat 12 (counted from the left, looking at the court).
"""

import math
from dataclasses import dataclass

# zone name -> (side of the hall, sector code prefix, target seats per sector)
STANDS = {
    "VIP": ("north", "V", 150),
    "Main stand": ("south", "M", 220),
    "End stand": ("ends", "", 170),
}
MAX_SECTORS_PER_SIDE = 6
MIN_PER_ROW, MAX_PER_ROW = 8, 30


@dataclass(frozen=True)
class Sector:
    code: str
    zone: str
    side: str  # north, south, west or east
    rows: tuple[int, ...]  # seats in each row, row 1 first

    @property
    def seats(self) -> int:
        return sum(self.rows)


def _split(total: int, parts: int) -> list[int]:
    """`total` cut into `parts` whole numbers that differ by at most one."""
    base, extra = divmod(total, parts)
    return [base + (i < extra) for i in range(parts)]


def _rows(seats: int) -> tuple[int, ...]:
    """Rows a sector of `seats` seats: wider than deep, never fewer than one row."""
    per_row = min(MAX_PER_ROW, max(MIN_PER_ROW, round(math.sqrt(seats * 2.2))))
    return tuple(_split(seats, max(1, math.ceil(seats / per_row))))


def _side(zone: str, side: str, prefix: str, capacity: int, target: int) -> list[Sector]:
    if capacity <= 0:
        return []
    count = min(MAX_SECTORS_PER_SIDE, capacity, max(1, round(capacity / target)))
    return [Sector(f"{prefix}{i + 1}", zone, side, _rows(n)) for i, n in enumerate(_split(capacity, count))]


def build_layout(zones: dict[str, int]) -> list[Sector]:
    """Sectors for the given {zone name: capacity}. A zone with an unknown name is treated like the Main stand."""
    sectors: list[Sector] = []
    for name, capacity in zones.items():
        side, prefix, target = STANDS.get(name, STANDS["Main stand"])
        if side == "ends":
            west, east = _split(capacity, 2)
            sectors += _side(name, "west", "W", west, target) + _side(name, "east", "E", east, target)
        else:
            sectors += _side(name, side, prefix, capacity, target)
    return sectors


def seat_codes(sector: Sector):
    for r, length in enumerate(sector.rows, start=1):
        for n in range(1, length + 1):
            yield f"{sector.code}-{r}-{n}"


def find_sector(layout: list[Sector], code: str) -> tuple[Sector, int, int] | None:
    """The sector, row and number a seat code points at, or None if no such seat exists."""
    parts = code.split("-")
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        return None
    row, number = int(parts[1]), int(parts[2])
    for sector in layout:
        if sector.code == parts[0] and 1 <= row <= len(sector.rows) and 1 <= number <= sector.rows[row - 1]:
            return sector, row, number
    return None
