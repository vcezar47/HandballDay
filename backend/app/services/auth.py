from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..errors import AuthError, ConflictError
from ..models import User
from ..repositories import RoleRepository, UserRepository
from ..security import DUMMY_HASH, hash_password, verify_password


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)

    def register(self, email: str, display_name: str, password: str) -> User:
        email = email.strip().lower()
        if self.users.get_by_email(email):
            raise ConflictError("Email is already registered")

        fan = self.roles.get_by_name("fan")
        user = User(
            email=email,
            display_name=display_name,
            password_hash=hash_password(password),
            role_id=fan.id,
        )
        try:
            self.users.add(user)
            self.db.commit()
        except IntegrityError:  # two requests raced for the same email
            self.db.rollback()
            raise ConflictError("Email is already registered")
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email.strip().lower())
        ok = verify_password(password, user.password_hash if user else DUMMY_HASH)
        # Same error for unknown email and wrong password.
        if not user or not ok:
            raise AuthError("Invalid email or password")
        return user
