"""Regenerate app/seed/clubs.json from the HandballManager repo.

    python tools/build_seed_data.py [path-to-HandballManager]

Run it only when the source data changes; the JSON is committed so the app, the tests and CI
do not need the game repo.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

SOURCE = Path(sys.argv[1] if len(sys.argv) > 1 else r"D:\Github Desktop\HandballManager")
CORE = SOURCE / "HandballManager.Core"
OUT = Path(__file__).resolve().parent.parent / "app" / "seed" / "clubs.json"

# club file -> logo key used by the game's kit colour tables ("Romania/<key>.png")
LOGO_KEY = {
    "baia_mare": "baiamare", "brasov": "coronabrasov", "craiova": "craiova",
    "csm_bucuresti": "csmbucuresti", "csm_iasi": "iasi", "csm_targu_mures": "targumures",
    "csu_stiinta_bucuresti": "stiintabucuresti", "dunarea_braila": "braila",
    "gloria_bistrita": "bistrita", "ramnicu_valcea": "valcea", "rapid_bucuresti": "rapidbucuresti",
    "slatina": "slatina", "targu_jiu": "targujiu", "zalau": "zalau",
}
COLOUR = re.compile(r'\["Romania/(\w+)\.png"\]\s*=\s*\("(#\w{6})",\s*"(#\w{6})"\)')


def colours() -> dict[str, tuple[str, str]]:
    table: dict[str, tuple[str, str]] = {}
    # Generated table first, hand-made overrides second so they win.
    for name in ("KitColours.Generated.cs", "KitColours.cs"):
        text = (CORE / "Engine2D" / name).read_text(encoding="utf-8")
        table.update({k: (a, b) for k, a, b in COLOUR.findall(text)})
    return table


def slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def main() -> None:
    kits = colours()
    clubs = []
    for path in sorted((CORE / "Data" / "InitialData2026" / "LigaFlorilor").glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        primary, secondary = kits[LOGO_KEY[path.stem]]
        clubs.append({
            "name": d["Name"],
            "slug": slugify(d["Name"]),
            "city": d["City"],
            "founded_year": d["FoundedYear"],
            "description": d["Description"],
            "venue": d["StadiumName"],
            "capacity": d["StadiumCapacity"],
            "primary_color": primary.lower(),
            "secondary_color": secondary.lower(),
        })
    OUT.write_text(json.dumps(clubs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(clubs)} clubs to {OUT}")


if __name__ == "__main__":
    main()
