"""Give an existing user a role (until the admin panel exists in M5).

    python -m app.set_role EMAIL fan|staff|admin [club-slug]

Staff need a club slug, for example: python -m app.set_role ana@example.com staff rapid-bucuresti
"""

import sys

from sqlalchemy.orm import Session

from .db import get_engine
from .repositories import ClubRepository, RoleRepository, UserRepository


def main(argv: list[str]) -> None:
    if len(argv) not in (2, 3):
        sys.exit(__doc__)
    email, role_name, club_slug = argv[0].strip().lower(), argv[1], (argv[2] if len(argv) == 3 else None)
    with Session(get_engine()) as db:
        user = UserRepository(db).get_by_email(email)
        role = RoleRepository(db).get_by_name(role_name)
        club = ClubRepository(db).get_by_slug(club_slug) if club_slug else None
        if not user:
            sys.exit(f"No user with email {email}")
        if not role:
            sys.exit(f"Unknown role {role_name!r}; use fan, staff or admin")
        if club_slug and not club:
            sys.exit(f"No club with slug {club_slug!r}")
        if role_name == "staff" and not club:
            sys.exit("Staff need a club slug")
        user.role_id = role.id
        user.club_id = club.id if role_name == "staff" else None
        db.commit()
    print(f"{email} is now {role_name}" + (f" of {club_slug}" if role_name == "staff" else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
