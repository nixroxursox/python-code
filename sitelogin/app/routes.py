import os
import sys
import json
from datetime import datetime, time
import datetime
from urllib.parse import parse_qsl
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    SimpleUser,
)
import jinja2
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader
from starlette.templating import Jinja2Templates
from starlette_wtf import StarletteForm, CSRFProtectMiddleware, csrf_protect

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import (
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
    JSONResponse,
    Response,
)
from starlette_wtf.csrf import (
    CSRFProtectMiddleware,
    csrf_protect,
    csrf_token,
    CSRFError
)

from starlette.datastructures import Headers
from starlette.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from forms import LoginForm, Register, Index
from user import User
from starlette.authentication import requires
from datetime import timedelta

from starlette_login.login_manager import Config, LoginManager, ProtectionLevel
from starlette_login.decorator import login_required
from decouple import config
from starlette.authentication import requires

sk = config('B_SESS_SECRET_KEY')


config = Config(
    SESSION_NAME_FRESH="_fresh",
    SESSION_NAME_ID="_id",
    SESSION_NAME_KEY="userId",
    SESSION_NAME_NEXT="next",
    EXEMPT_METHODS=("OPTIONS",),
    protection_level=ProtectionLevel.Basic,
    REMEMBER_COOKIE_NAME="_remember",
    REMEMBER_SECONDS_NAME="_remember_seconds",
    # Cookie configuration
    COOKIE_NAME="remember_token",
    COOKIE_DOMAIN="nix.onion",
    COOKIE_PATH="/",
    COOKIE_SECURE=False,
    COOKIE_HTTPONLY=True,
    COOKIE_SAMESITE=True,
    COOKIE_DURATION=timedelta(days=0),
)
login_manager = LoginManager(
    redirect_to="login_page", config=config, secret_key=sk
)

env = Environment(loader=FileSystemLoader("templates"))
templates = Jinja2Templates(env=env)


request = Request
response = Response

HOME_PAGE = "You are logged in as {{ user.username }}"
LOGIN_PAGE = """
<h4>{error}<h4>
<form method="POST">
<label>username <input name="username"></label>
<label>Password <input name="password" type="password"></label>
<label>pinCode<input name="pinCode" type="password"></label>
<button type="submit">Login</button>
</form>
"""

# async def login_page(request: Request):
#     if request.user.is_authenticated:
#         request.session["username"] = username
#         return RedirectResponse("/", status_code=302)
#     error = None
#     if request.method == "POST":
#         uu = User()
#         form = await request.form()
#         user = uu.find(form["username"])
#         if user in None or False:
#             error = "Invalid username"

#         elif uu.checkPass(form["password"]) is True:
#             # Login user - create user session
#             await login_user(request, user)
#             return RedirectResponse("/", status_code=302)
#         else:
#             error = "Invalid username password"
#     return template.TemplateResponse(
#         "/login.html", context={"request": request, "error": error}
#     )

# async def login_page(request: Request) -> Response:
#     form_data = await request.form()
#     username = form_data["username"]
#     regenerate_session_id(request)
#     return RedirectResponse("/profile", 302)
#     await load_session(username)
#     request.session["username"] = username
#     regenerate_session_id(request)
#     return RedirectResponse("/profile", 302)


async def login_page(request: Request):
    error = ""
    if request.user.is_authenticated:
        return RedirectResponse("/", 302)
    if request.method == "POST":
        uu = User()
        body = (await request.body()).decode()
        data = dict(parse_qsl(body))
        for k, v in data.items():
            print(k, v)
        un = data["username"]
        pw = data["password"]
        pin = data["pinCode"]
        user = uu.find(un)
        if user is True:
            pwc = uu.checkPass(un, pw)
            if pwc is True:
                print("password match")
                pin = uu.checkPin(un, pin)
                print("pinCode match")
                if pin is True:
                    return RedirectResponse("/profile", 302)
            error = "You must fill out all fields"
            return templates.TemplateResponse('/loginForm.html', {'request': request})
        else:
            await login_user(request, user)
            return RedirectResponse("/", 302)
    # return HTMLResponse(LOGIN_PAGE.format(error=error))
    return templates.TemplateResponse('/loginForm.html', {'request': request})


@requires("authenticated")
async def logout_page(request: Request):
    if request.user.is_authenticated:
        content = "Logged out"
        await logout_user(request)
    else:
        content = "You not logged in"
    return PlainTextResponse(content)


# async def home_page(request: Request):
#     await load_session(request)
#     if request.user.is_authenticated:
#         content = f"You are logged in as {request.user.username}"
#         return templates.TemplateResponse(request, "index.html")
#     else:
#         content = "You are not logged in"
#     return PlainTextResponse(content=content)


async def homepage(request: Request) -> Response:
    template = "index.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context, status_code=200)


# @login_required
# @admin_only
@requires("authenticated", "admin")
async def admin_page(request: Request):
    return PlainTextResponse(
        f"You are an admin and logged in as {request.user.username}"
    )


# async def register(request: Request):
#     message = "Checking for registration..."
#     if request.method == "POST":
#         body = (await request.body()).decode()
#         data = dict(parse_qsl(body))
#         if data is not None:
#             un = data["username"]
#             password = data["password"]
#             nickName = data["nickName"]
#             pinCode = data["pinCode"]
#             uu = User()
#             if uu.find(un) is True:
#                 context = "Username is in Use...  Please choose another."
#                 return templates.TemplateResponse("auth/register.html", context=context)
#             result = uu.create(un, password, pinCode, nickName)
#             error = result.nInserted
#             context = {"request": request, "error": error}
#             return templates.TemplateResponse("auth/login.html", context=context)
#     else:
#         error = "fuuuuuck you suck"
#         context = {"request": request, "error": error}
#         return templates.TemplateResponse("auth/register.html", context=context)

async def register(request: Request):
    """GET|POST /register: create account form handler
    """
    # initialize form
    form = await Register.from_formdata(request)
    
    # validate form
    if await form.validate_on_submit():
        # TODO: Save account credentials before returning redirect response
        return RedirectResponse(url='/profile', status_code=303)

    template = env.get_template("/regForm.html")
    html = template.render(form=form)
    # return response

    # return form html
    context = {'request': request, 'form': form}
    status_code = 422 if form.errors else 200

    return templates.TemplateResponse('/regForm.html',
                                      context=context,
                                      status_code=status_code)


@requires("authenticated")
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


@requires("authenticated")
async def session(request: Request) -> HTMLResponse:
    """Access this view (GET "/app") to display session contents."""
    return HTMLResponse(
        f"<div>session data: {json.dumps(request.session)}</div>"
        "<ol>"
        '<li><a href="/set">set example data</a></li>'
        '<li><a href="/clean">clear example data</a></li>'
        "</ol>"
    )


async def set_time(request: Request) -> RedirectResponse:
    """Access this view (GET "/set") to set session contents."""
    request.session["date"] = datetime.datetime.now().isoformat()
    return RedirectResponse("/session")


async def clean(request: Request) -> RedirectResponse:
    """Access this view (GET "/clean") to remove all session contents."""
    request.session.clear()
    return RedirectResponse("/session ")


templates = Jinja2Templates(directory="templates")


async def error(request):
    """
    An example error. Switch the `debug` setting to see either tracebacks or 500 pages.
    """
    raise RuntimeError("Oh no")


async def not_found(request: Request, exc: HTTPException):
    """
    Return an HTTP 404 page.
    """
    template = "404.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context, status_code=404)


async def server_error(request: Request, exc: HTTPException):
    """
    Return an HTTP 500 page.
    """
    template = "500.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context, status_code=500)


async def index_view(request):
    session_data = request.session
    return JSONResponse(session_data)


async def loginForm(request: Request):

    # initialize form
    form = await LoginForm.from_formdata(request)

    # validate form
    if await form.validate_on_submit():
        # TODO: Save account credentials before returning redirect response
        return RedirectResponse(url='/profile', status_code=303)
    

    template = env.get_template("index.html")
    html = template.render(form=form)
    # return response

    # return form html
    context = {'request': request, 'form': form}
    status_code = 422 if form.errors else 200

    return templates.TemplateResponse('/index.html',
                                      context=context,
                                      status_code=status_code)


@csrf_protect
async def index(request):
    form = await Index.from_formdata(request)
    
    if form.validate_on_submit():
        return PlainTextResponse('SUCCESS')
    template = env.get_template("index.html")
    html = template.render(form=form)
    return HTMLResponse(html)