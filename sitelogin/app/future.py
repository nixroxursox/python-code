import asyncio
import starlette
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import (
    JSONResponse,
    HTMLResponse,
    PlainTextResponse,
    Response,
    RedirectResponse,
)
from routes import login_page, logout_page, home_page, session, profile, register, error
from app import admin, index_view
from starlette.staticfiles import StaticFiles

request = Request
response = Response
session_store = CookieStore(secret_key="secret")


async def myFuture(future):
    await asyncio.sleep(1)
    future.set_result("My Future Has Completed")


async def main():
    future = asyncio.Future()
    await asyncio.ensure_future(myFuture(future))
    print(future.result())


middleware = [
    Middleware(
        SessionMiddleware,
        store=session_store,
        cookie_https_only=False,
        lifetime=300,
        serializer=Serializer,
    ),
    Middleware(SessionAutoloadMiddleware, paths=["/"]),
]

routes = [
    Route("/index", index_view),
    Route("/admin", admin),
    Route("/login", login_page, methods=["GET", "POST"]),
    Route("/logout", logout_page, methods=["POST"]),
    Route("/profile", profile, methods=["GET"], name="profile"),
    Route("/", home_page, methods=["GET"], name="home"),
    Route("/register", register, methods=["GET", "POST"], name="register"),
    Route("/app", session, methods=["GET"], name="session"),
    Mount("/static", app=StaticFiles(directory="static"), name="static"),
    Mount("/style", app=StaticFiles(directory="style"), name="style"),
    Mount("/images", app=StaticFiles(directory="images"), name="images"),
    Route("/error", error),
]


async def app(self, **kwargs):
    self.app = Starlette()
    app.add_middleware = middleware
    app.add_route = routes
    assert scope["type"] == "http"
    request = Request(scope, receive)
    content = "%s %s %s" % (request.method, request.url.path, request.headers)
    response = Response(content, media_type="text/plain")
    await response(scope, receive, send)
    return app


loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(app(request))
finally:
    loop.close()
