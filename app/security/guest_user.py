"""Helpers for creating and reading guest cart cookies."""

from uuid import uuid4

from fastapi import Request, Response

GUEST_COOKIE = "guest_id"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30


def get_or_create_guest_id(request: Request, response: Response) -> str:
    guest_id = request.cookies.get(GUEST_COOKIE)

    if guest_id:
        return guest_id

    guest_id = str(uuid4())

    response.set_cookie(
        key=GUEST_COOKIE,
        value=guest_id,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,  # TODO change to True when we deploy
    )

    return guest_id
