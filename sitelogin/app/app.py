from decouple import config
import uvicorn
import jinja2
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader
from starlette.templating import Jinja2Templates
from starlette.applications import Starlette
from starlette.requests import Request, HTTPConnection
from starlette.responses import (
    JSONResponse,
    RedirectResponse,
    PlainTextResponse,
    Response,
    HTMLResponse,
)
from starlette_wtf.csrf import (
    CSRFProtectMiddleware,
    generate_csrf,
    csrf_protect,
    csrf_token
)
from starlette.staticfiles import StaticFiles
from starlette.routing import Route, Mount
from starlette.endpoints import HTTPEndpoint
from starlette.exceptions import HTTPException
from starlette_login.login_manager import LoginManager
from starlette.middleware import Middleware
from starlette_session.backends import BackendType
from starlette_session import SessionMiddleware
from pymemcache.client.base import PooledClient
from endpoints import setup_session, view_session, clear_session
from utils import JsonSerde
from routes import (
    homepage,
    login_page,
    logout_page,
    admin_page,
    register,
    index_view,
    loginForm,
    index
)


request = Request
response = Response

sk = config("SECRET_KEY")
env = Environment(loader=FileSystemLoader("templates"))
templates = Jinja2Templates(env=env)


login_manager = LoginManager(redirect_to="login_page", secret_key=sk)
mclient = PooledClient(server="dockerswarm-memcached-1",
                       serde=JsonSerde(), connect_timeout=10, timeout=30)


routes=[
    Route("/", homepage, name="homepage"),
    Route("/login", loginForm,
            methods=["GET", "POST"], name="loginForm"),
    Route("/logout", logout_page, methods=["GET", "POST"], name="logout"),
    Route("/admin", admin_page),
    Route("/setup_session", endpoint=setup_session),
    Route("/clear_session", endpoint=clear_session),
    Route("/view_session", endpoint=view_session),
    Mount("/static", app=StaticFiles(directory="static"), name="static"),
    Mount("/style", app=StaticFiles(directory="style"), name="style"),
    Mount("/images", app=StaticFiles(directory="images"), name="images"),
    Route('/register', register, methods=['GET','POST'], name='register'),
    Route("/index",index,methods=["GET"], name="index")
]

app = Starlette(
    debug=True,
    routes=routes
    
)

app.state.login_manager = login_manager


# async def run(app, uds="/tmp/starlette.sock") -> Starlette:

app.add_middleware(
    SessionMiddleware,
    secret_key=sk,
    backend_type=BackendType.memcache,
    cookie_name = '_cookie',
    backend_client=mclient
)
# app.add_middleware(
#     AuthenticationMiddleware,
#     backend=SessionAuthBackend(login_manager),
#     login_manager=login_manager,
#     allow_websocket = False
# )

app.add_middleware(
    CSRFProtectMiddleware,
    csrf_secret=sk,
    enabled=True,
    csrf_field_name = 'csrf_token',
    csrf_time_limit = 300
)


# async def homepage(request):
#     return JSONResponse({'hello': 'world'})

# routes = [
#     Route("/", endpoint=homepage),
#     Route("/login", methods=["GET", "POST"], endpoint="login")
# ]

# def startup():
#     db = dataBase.conf("read")
#     rdb = db["luser"]

# app = Starlette(debug=True, on_startup=[startup], routes=routes)


if __name__ == "__main__":
    config = uvicorn.Config(
        "app:app",
        log_level="debug",
        uds="/tmp/starlette.sock",
        reload=False,
        loop="uvloop",
        factory=False,
        workers=50,
    )
    server = uvicorn.Server(config)
    server.run()



## . /home/starlette/.python/bin/activate