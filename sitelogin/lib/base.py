import asyncio
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie


from typing import Callable, Optional, TYPE_CHECKING, Union

from .globals import current_app

if TYPE_CHECKING:
    from .wrappers import Response  # noqa: F401


def redirect(location: str, status_code: int = 301) -> "Response":
    body = f"""
<!doctype html>
<title>Redirect</title>
<h1>Redirect</h1>
You should be redirected to <a href="{location}">{location}</a>, it not please click the link
    """

    return current_app.response_class(
        body,
        status=status_code,
        headers={"Location": location},
    )


def create_cookie(
    key: str,
    value: str = "",
    max_age: Optional[Union[int, timedelta]] = None,
    expires: Optional[datetime] = None,
    path: str = "/",
    domain: Optional[str] = None,
    secure: bool = False,
    httponly: bool = False,
) -> SimpleCookie:
    """Create a Cookie given the options set

    The arguments are the standard cookie morsels and this is a
    wrapper around the stdlib SimpleCookie code.
    """
    cookie = SimpleCookie()  # type: ignore
    cookie[key] = value
    cookie[key]["path"] = path
    cookie[key]["httponly"] = httponly  # type: ignore
    cookie[key]["secure"] = secure  # type: ignore
    if isinstance(max_age, timedelta):
        cookie[key]["max-age"] = f"{max_age.total_seconds():d}"  # type: ignore
    if isinstance(max_age, int):
        cookie[key]["max-age"] = str(max_age)
    if expires is not None:
        cookie[key]["expires"] = expires.astimezone(timezone.utc).strftime(
            "%a, %d-%b-%Y %T"
        )
    if domain is not None:
        cookie[key]["domain"] = domain
    return cookie


def ensure_coroutine(func: Callable) -> Callable:
    return func if asyncio.iscoroutinefunction(func) else asyncio.coroutine(func)
