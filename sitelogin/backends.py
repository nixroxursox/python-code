from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    UnauthenticatedUser,
)
import asyncio
import typing as t

from starlette.requests import HTTPConnection

from login_manager import LoginManager
from mixins import UserMixin
from utils import create_identifier


class BaseAuthenticationBackend:
    # name: str = None

    async def authenticate(self, request: HTTPConnection):
        ...  # pragma: no cover


class SessionAuthBackend(BaseAuthenticationBackend):
    def __init__(self, login_manager: LoginManager):
        self.login_manager = login_manager

    async def authenticate(self, conn: HTTPConnection) -> t.Optional[UserMixin]:
        # Load user from session
        config = self.login_manager.config
        remember_cookie = config.REMEMBER_COOKIE_NAME
        session_fresh = config.SESSION_NAME_FRESH

        session = conn.session.get(config.SESSION_NAME_ID)
        identifier = create_identifier(conn)

        if identifier != session:
            if self.login_manager.protection_is_strong():
                # Strong protection
                for key in config.session_keys:
                    conn.session.pop(key, None)
                conn.session[remember_cookie] = "clear"
            else:
                conn.session[session_fresh] = False
        user_id = conn.session.get(config.SESSION_NAME_KEY)

        if user_id is None and conn.session.get(remember_cookie) != "clear":
            cookie = conn.cookies.get(config.COOKIE_NAME)
            if cookie:
                user_id = self.login_manager.get_cookie(cookie)
                conn.session[session_fresh] = False

        if user_id is None:
            return None
        elif asyncio.iscoroutinefunction(self.login_manager.user_loader):
            user = await self.login_manager.user_loader(conn, user_id)
        else:
            user = self.login_manager.user_loader(conn, user_id)
        return user


class ModelAuthBackend(AuthenticationBackend):
    def get_user(self, conn: HTTPConnection):
        user_id = conn.session.get("user")
        if user_id:
            try:
                return User.query.get(user_id)
            except:
                conn.session.pop("user")

    async def authenticate(self, conn: HTTPConnection):
        user = self.get_user(conn)
        if user and user.is_authenticated:
            scopes = ["authenticated"] + sorted([str(s) for s in user.scopes])
            return AuthCredentials(scopes), user
        scopes = ["unauthenticated"]
        return AuthCredentials(scopes), UnauthenticatedUser()
