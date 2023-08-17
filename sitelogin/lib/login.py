from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import Route

from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware
from starsessions.session import regenerate_session_id, HTTPConnection
from starsessions import get_session_id, get_session_metadata, generate_session_id


async def homepage(request: Request) -> Response:
    """Access this view (GET "/") to display session contents."""
    return HTMLResponse(
        """
    <form method="post" action="/login">
    <label> Username <input type="text" name="username"> </label>
    <button type="submit">Sign in</button>
    </form>
    <a href="/profile">My profile</a>
    """
    )


async def login(request: Request) -> Response:
    form_data = await request.form()
    username = form_data["username"]
    s = request.session()
    if s:
        s["id"] = generate_session_id()
        s["username"] = username
        return RedirectResponse("/profile", 302)



async def logout(request: Request) -> Response:
    request.session.clear()
    return RedirectResponse("/", 302)


async def profile(request: Request) -> Response:
    username = request.session.get("username")
    if not username:
        return RedirectResponse("/", 302)

    return HTMLResponse(
        """
    <p>Hi, {username}!</p>
    <form method="post" action="/logout">
    <button type="submit">logout</button>
    </form>
    """.format(
            username=username
        )
    )


# routes = [
#     Route("/", endpoint=homepage),
#     Route("/login", endpoint=login, methods=["POST"]),
#     Route("/logout", endpoint=logout, methods=["POST"]),
#     Route("/profile", endpoint=profile),
# ]