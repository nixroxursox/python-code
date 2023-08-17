from starlette.applications import Starlette
import datetime
import asyncio
from starlette.middleware import Middleware
from starlette.requests import Request, Scope
from starlette.responses import (
    JSONResponse,
    HTMLResponse,
    PlainTextResponse,
    Response,
    RedirectResponse,
)
from starlette.routing import Route, Mount, Router
from starlette.templating import Jinja2Templates
import uvicorn
from uvicorn.main import Server
from uvicorn.middleware.asgi2 import ASGI2Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    SimpleUser,
)
from starlette.middleware.authentication import AuthenticationMiddleware
import httptools
from starlette_login.login_manager import LoginManager
from starlette.staticfiles import StaticFiles
from starlette_login.backends import SessionAuthBackend
from decouple import config
from starlette_wtf import StarletteForm, CSRFProtectMiddleware, csrf_protect
from routes import (
    register,
    home_page,
    login_page,
    logout_page,
    profile,
    session,
    error,
    not_found,
    server_error,
    set_time,
)
from utils import (
    login_user,
    logout_user,
    encode_cookie,
    decode_cookie,
    make_next_url,
    create_identifier,
)
from starlette_login import login_manager
from middleware import BasicAuthBackend
from endpoints import login, view_session, clear_session, setup_session
from starlette_session import SessionMiddleware
from starlette_session.backends import BackendType
from starlette.endpoints import HTTPEndpoint
from pymemcache.client.base import PooledClient
from utils import JsonSerde
from pymemcache.serde import python_memcache_deserializer, python_memcache_serializer


serializer = python_memcache_serializer
deserializer = python_memcache_deserializer

mclient = PooledClient(
    server="localhost:11211",
    serializer=serializer,
    deserializer=deserializer,
    connect_timeout=60,
    timeout=30,
    serde=JsonSerde,
)

sk = config("B_SESS_SECRET_KEY")


request = Request
response = Response
scope = Scope
router = Router

template = Jinja2Templates(directory="templates")
templates = Jinja2Templates(directory="templates")

login_manager = LoginManager(redirect_to="login", secret_key=sk)
template = Jinja2Templates(directory="templates")


def startup():
    login_manager = ("login_manager",)
    login_route = ("login",)
    excluded_dirs = ["/favicon.ico"]


async def index_view(request):
    if request.session is not None:
        session_data = request.session
        return JSONResponse(session_data)


# async def admin(request):
#     awai(request)

exception_handlers = {404: not_found, 500: server_error}


async def create_app() -> Starlette:
    starapp = Starlette(scope, receive, send)
    assert scope["type"] == "http"
    middleware = (
        Middleware(
            SessionMiddleware,
            secret_key=sk,
            cookie_name="cookie_",
            backend_type=BackendType.memcache,
            backend_client=mclient,
        ),
        Middleware(AuthenticationMiddleware, backend=BasicAuthBackend()),
        Middleware(CSRFProtectMiddleware, csrf_secret=sk),
        Middleware(ASGI2Middleware),
    )
    starapp.add_middleware = middleware

    routes = (
        Route("/index", index_view),
        Route("/admin", admin),
        Route("/login", login_page, methods=["GET", "POST"]),
        Route("/elogin", login, methods=["GET", "POST"]),
        Route("/logout", logout_page, methods=["POST"]),
        Route("/profile", profile, methods=["GET"], name="profile"),
        Route("/", home_page, methods=["GET"], name="home"),
        Route("/register", register, methods=["GET", "POST"], name="register"),
        Route("/app", session, methods=["GET"], name="session"),
        Route("/set", set_time, methods=["GET"], name="set_time"),
        Mount("/static", app=StaticFiles(directory="static"), name="static"),
        Mount("/style", app=StaticFiles(directory="style"), name="style"),
        Mount("/images", app=StaticFiles(directory="images"), name="images"),
        Route("/setup_session", endpoint=setup_session),
        Route("/clear_session", endpoint=clear_session),
        Route("/view_session", endpoint=view_session),
        Route("/error", error),
    )
    starapp.add_route = routes
    return starapp


def run(app):
    loop = asyncio.get_event_loop()
    handler = app.make_handler()
    f = loop.create_server(handler)
    srv = loop.run_until_complete(f)
    print("serving on", srv.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(handler.finish_connections(1.0))
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(app.finish())
    loop.close()


# async def main():
if __name__ == "__main__":
    config = uvicorn.Config(
        # "app:app", log_level="debug",  uds="/tmp/starlette.sock", reload=True, loop="uvloop", workers=5
        "app:create_app",
        log_level="debug",
        uds="/tmp/starlette.sock",
        reload=False,
        loop="uvloop",
        factory=True,
        workers=50,
    )
    app = create_app()
    server = uvicorn.Server(config)
    server.run()
    run(app)


# if __name__ == "__main__":
#     def uvloop_setup(use_subprocess: bool = True) -> None:
#         asyncio.run(main())
#         #asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

#     #asyncio.get_event_loop().create_task(main())
#         asyncio.Runner.run(main())

# # if __name__ == "__main__":
# #     def __init__(self, app) -> None:
# #         serve.init(name=app)
# #         self.app = get_app()
# #         await self.app.fetch_config_from_master()
# #  # Start running the HTTP server on the event loop.
# #         asyncio.get_event_loop().create_task(self.run())
