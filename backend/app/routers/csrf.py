from fastapi import APIRouter, Request, Response

from ..config import get_config
from ..security.csrf import COOKIE, is_valid_token, new_token

router = APIRouter(prefix="/api", tags=["csrf"])


@router.get("/csrf")
def csrf(request: Request, response: Response):
    token = request.cookies.get(COOKIE)
    if not is_valid_token(token):  # keep a valid one so several tabs share it
        token = new_token()
        response.set_cookie(
            COOKIE, token, httponly=True, samesite="lax", secure=get_config().secure_cookies,
            max_age=get_config().session_max_age,
        )
    return {"csrf_token": token}
