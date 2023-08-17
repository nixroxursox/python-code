import contextlib  # .applications import Starlette

# import uvicorn
# from db.dB import dataBase, q
import jinja2
import starsessions
import endpoints
#import redis3
import uvicorn
from exceptions import ImproperlyConfigured, not_found, server_error
from decouple import config
from jinja2 import Environment, FileSystemLoader
from nacl import encoding, exceptions, pwhash, utils
from starlette.applications import Request, Response, Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route
from starlette.templating import Jinja2Templates
from starlette.types import Message
from starlette_login.login_manager import Config, LoginManager, ProtectionLevel
from starlette_login.middleware import AuthenticationMiddleware
from starsessions import (CookieStore, SessionStore, SessionAutoloadMiddleware,
                          SessionMiddleware, InMemoryStore)
from starsessions.session import regenerate_session_id
from uvicorn.middleware.message_logger import MessageLoggerMiddleware


from db.dB import dataBase, q
# from headers import ProxyHeadersMiddleware
# from backends import SessionAuthBackend, ModelAuthBackend
# from middleware import AuthenticationMiddleware, CustomHeaderMiddleware
from routes import admin_page, home_page, login_page, logout_page, register, session, profile
from user import User, userList


sk = config("SECRET_KEY")

#login_manager.set_user_loader()

login_manager = LoginManager(redirect_to="login", secret_key=sk)
template = Jinja2Templates(directory="templates")

cookie_name = "ring_cookie"
session_store = InMemoryStore()


def startup():
    uu = User()
    config = Config(protection_level=ProtectionLevel.Strong)
    login_manager = LoginManager(
        redirect_to='login', secret_key=sk, config=config
    )

    async def app(scope, receive, send):
        assert scope['type'] == 'http'
        request = Request(scope, receive)
        content = '%s %s' % (request.method, request.url.path)
        response = Response(content, media_type='text/plain')
        await response(scope, receive, send)
    # app.state.login_manager = login_manager


app = Starlette(
    debug=True,
    routes=[
        Route('/', home_page, methods=['GET'], name='home'),
        Route('/login', endpoints.Login, methods=['GET', 'POST'], name='login'),
        Route('/logout', logout_page, methods=['GET', 'POST'], name='logout'),
        Route('/admin', admin_page, methods=['GET'], name='admin'),
        Route('/register', register, methods=['GET', 'POST'], name='register'),
        Route('/app', session, methods=['GET'], name='session'),
        Route("/profile", endpoint=profile),
        Mount('/static', app=StaticFiles(directory='static'), name='static'),
        Mount('/style', app=StaticFiles(directory='style'), name='style'),
        Mount('/images', app=StaticFiles(directory='images'), name='images'),
        Route(
            "/login", endpoint=endpoints.Login, methods=["GET", "POST"], name="login"
        ),
        Route(
            "/password/change",
            endpoint=endpoints.ChangePassword,
            methods=["GET", "POST"],
            name="password_change",
        ),
        Route(
            "/password/reset",
            endpoint=endpoints.PasswordReset,
            methods=["GET", "POST"],
            name="password_reset",
        ),
        Route(
            "/password/reset/done",
            endpoint=endpoints.PasswordResetDone,
            methods=["GET"],
            name="password_reset_done",
        ),
        Route(
            "/password/reset/{uidb64:str}/{token:str}",
            endpoint=endpoints.PasswordResetConfirm,
            methods=["GET", "POST"],
            name="password_reset_confirm",
        ),
        Route(
            "/password/reset/complete",
            endpoint=endpoints.PasswordResetComplete,
            methods=["GET"],
            name="password_reset_complete",
        )
        #        Route("/setup_session", endpoint=setup_session),
        #        Route("/clear_session", endpoint=clear_session),
        #        Route("/view_session", endpoint=view_session)
    ],
    middleware=[
        Middleware(CORSMiddleware, allow_origins=['*']),
        Middleware(SessionAutoloadMiddleware, paths=['/admin', '/app']),

        Middleware(MessageLoggerMiddleware),
        Middleware(SessionMiddleware,
        store=session_store,
        #rolling=True,
        cookie_https_only=False,
        lifetime=10
        ),
        Middleware(SessionAutoloadMiddleware),
        # Middleware(BaseHTTPMiddleware),
        Middleware(
            AuthenticationMiddleware,
            backend=SessionAuthBackend,
            login_manager=login_manager,
            excluded_dirs=['/favicon.ico']

        ),
        Middleware(ProxyHeadersMiddleware),
        Middleware(CustomHeaderMiddleware)
        # Middleware(HTTPSRedirectMiddleware)
    ],
    on_startup=[startup]
)
# async def app(scope, receive, send):
#     assert scope['type'] == 'http'
#     request = Request(scope, receive)
#     content = '%s %s' % (request.method, request.url.path)
#     response = Response(content, media_type='text/plain')
#     await response(scope, receive, send)

#     return JSONResponse({'hello': 'world'})

# routes = [
#     Route("/", endpoint=homepage),
#     Route("/login", methods=["GET", "POST"], endpoint="login")
#
# app = Starlette(debug=True, on_startup=[startup], routes=routes)


# async def login(request):
#     if request.method == 'GET':
#         return templates.TemplateResponse("auth/login.html", {"request": request})
#     else:
#         fUser = request.form["username"]
#         user = await rdb.find({}, {q.findUser})


if __name__ == "__main__":
    config = uvicorn.Config(
        "main:app", log_level="debug",  uds="/tmp/starlette.sock", reload=True
    )
    server = uvicorn.Server(config)
    server.run()
