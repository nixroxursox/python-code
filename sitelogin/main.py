# from starlette.applications import Starlette
# from starlette.responses import JSONResponse, PlainTextResponse, HTMLResponse
# import uvicorn
# from db.dB import dataBase, queries
# from starlette.routing import Route, Mount
# from starlette.templating import Jinja2Templates
# from starlette.requests import Request
# from starlette.responses import Response
from decouple import config
from starlette.applications import Starlette, Request, Response
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Route
import uvicorn
from db.dB import dataBase, queries
from starlette_login.backends import SessionAuthBackend
from starlette_login.login_manager import LoginManager
from starlette_login.middleware import AuthenticationMiddleware
import lib.logging as logging
from user import userList
from cookie import Session
import lib.routes as routes
import lib.requests as requests
import lib.responses as responses
from lib.routes import home_page, login_page, logout_page, protected_page
from starlette.templating import Jinja2Templates

sk = config("SECRET_KEY")


login_manager = LoginManager(redirect_to="login", secret_key=sk)
template = Jinja2Templates(directory="templates")


login_manager = LoginManager(redirect_to="login", secret_key=sk)
login_manager.set_user_loader(userList.usersAll())


login_manager = LoginManager(redirect_to="login", secret_key=sk)
template = Jinja2Templates(directory="templates")

app = Starlette(
    middleware=[
        Middleware(SessionMiddleware, secret_key=sk),
        Middleware(
            AuthenticationMiddleware,
            backend=SessionAuthBackend(login_manager),
            login_manager=login_manager,
            # login_route='login',
            allow_websocket=False,
        ),
    ],
    routes=[
        Route("/", home_page, name="home"),
        Route("/login", login_page, methods=["GET", "POST"], name="login"),
        Route("/logout", logout_page, name="logout"),
        Route("/protected", protected_page, name="protected"),
    ],
)
app.state.login_manager = login_manager


templates = Jinja2Templates(directory="templates", autoescape=False, auto_reload=True)


# async def homepage(request):
#     return JSONResponse({'hello': 'world'})

# routes = [
#     Route("/", endpoint=homepage),
#     Route("/login", methods=["GET", "POST"], endpoint="login")
# ]

# def startup():
#     db = dataBase.Config("read")
#     rdb = db["luser"]


# app = Starlette(debug=True, on_startup=[startup], routes=routes)

async def login(request):
    if request.method == 'GET':
        return templates.TemplateResponse("auth/login.html", {"request": request})
    else:
        fUser = request.form["username"]
        user = await rdb.find({}, {queries.findUser})


if __name__ == "__main__":
    config = uvicorn.Config(
        "main:app", port=8000, log_level="debug", uds="/tmp/starlette.sock"
    )
    server = uvicorn.Server(config)
    server.run()
