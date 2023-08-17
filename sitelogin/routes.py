import os
import sys
from datetime import datetime, time
import datetime
from urllib.parse import parse_qsl

import jinja2
from jinja2 import Environment, FileSystemLoader
from starlette.applications import Request, Response, Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from starlette_login.decorator import login_required
from starlette_login.utils import login_user, logout_user
from starsessions import load_session
from starlette_login.decorator import login_required

from admin import admin_only
from user import User


template = Jinja2Templates(directory="templates")

request = Request
response = Response

HOME_PAGE = "You are logged in as {{ user.username }}"
LOGIN_PAGE = """
<h4>{error}<h4>
<form method="POST">
<label>username <input name="username"></label>
<label>Password <input name="password" type="password"></label>
<button type="submit">Login</button>
</form>
"""
env = jinja2.Environment()
templates = Jinja2Templates(directory="templates", autoescape=False, auto_reload=True)


async def login_page(request: Request):
    if request.user.is_authenticated:
        request.session["username"] = username
        return RedirectResponse("/", status_code=302)
    error = None
    if request.method == "POST":
#        body = (await request.body()).decode()
#        data = dict(parse_qsl(body))
        form_data = await request.form()
        user = form_data["username"]
        pw = form_data["password"]
        pin = form_data["pinCode"]
        uu = User()
        uu.get_userId(user)       
        if user in None or True:
            error = "Invalid or non-existant username.  Please create an account"
            return template.TemplateResponse(
            "auth/register.html", context={"request": request, "error": error}
            )
        elif:
            uu.checkPass(form["password"]) is True and uu.checkPin(form["pinCode"]) is True:
            await login_user(request, user)
            session_lmoad(user)
            return RedirectResponse("/", status_code=302)
        else:
            error = "Invalid password or pin  code"
            return template.TemplateResponse(
            "auth/login.html", context={"request": request, "error": error}
            )


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
# @app.route("/register", methods=["GET", "POST"])


@login_required
@admin_only
async def admin_page(request: Request):
    return PlainTextResponse(
        f"You are an admin and logged in as {request.user.username}"
    )


async def register(request: Request):
    message = "Checking for registration..."
    if request.method == "POST":
        body = (await request.body()).decode()
        data = dict(parse_qsl(body))
        if data is not None:
            un = data["username"]
            password = data["password"]
            nickName = data["nickName"]
            pinCode = data["pinCode"]
            uu = User()
            if uu.find(un) is True:
                context = "Username is in Use...  Please choose another."
                return templates.TemplateResponse("auth/register.html", context=context)
            result = uu.create(un, password, pinCode, nickName)
            error = result.nInserted
            context = {"request": request, "error": error}
            return templates.TemplateResponse("auth/login.html", context=context)
    else:
        error = "fuuuuuck you suck"
        context = {"request": request, "error": error}
        return templates.TemplateResponse("auth/register.html", context=context)



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
