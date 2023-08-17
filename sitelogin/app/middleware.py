import typing as t

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    SimpleUser,
    UnauthenticatedUser,
)
from starlette_login.login_manager import LoginManager
import json
import typing
from typing import Dict
from nacl.encoding import URLSafeBase64Encoder
from decouple import config

import itsdangerous
from itsdangerous.exc import BadTimeSignature, SignatureExpired
from starlette.datastructures import MutableHeaders, Secret
import datetime
import re

from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send

b64_encode = URLSafeBase64Encoder.encode
b64_decode = URLSafeBase64Encoder.decode

sk = config("SECRET_KEY")


class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        if "Authorization" not in conn.headers:
            return

        auth = conn.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != "basic":
                return
            decoded = b64_decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
            raise AuthenticationError("Invalid basic auth credentials")

        username, _, password = decoded.partition(":")
        # TODO: You'd want to verify the username and password here.
        return AuthCredentials(["authenticated"]), SimpleUser(username)


class AuthenticationMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        backend: BasicAuthBackend,
        login_manager: LoginManager,
        excluded_dirs: t.List[str] = None,
        allow_websocket: bool = False,
    ):
        self.app = app
        self.backend = backend
        self.excluded_dirs = excluded_dirs or []
        self.login_manager = login_manager
        self.secret_key = sk
        self.allow_websocket = allow_websocket

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.allow_websocket is False and scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        elif scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Excluded prefix path. E.g. /static
        for prefix_dir in self.excluded_dirs:
            if scope["path"].startswith(prefix_dir):
                await self.app(scope, receive, send)
                return

        conn = HTTPConnection(scope=scope, receive=receive)

        user = await self.backend.authenticate(conn)
        if not user or user.is_authenticated is False:
            conn.scope["user"] = self.login_manager.anonymous_user_cls()
        else:
            conn.scope["user"] = user

        async def custom_send(message: Message):
            user_ = conn.scope["user"]
            if user and user_.is_authenticated:
                operation = conn.session.get(
                    self.login_manager.config.REMEMBER_COOKIE_NAME
                )
                if operation == "set":
                    message = self.login_manager.set_cookie(
                        message=message, user_id=user_.identity
                    )
                elif operation == "clear":
                    try:
                        del conn.cookies[self.login_manager.config.COOKIE_NAME]
                    except KeyError:
                        pass
            await send(message)

        await self.app(scope, receive, custom_send)
        return


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Custom"] = "Example"
        return response


class LoadGuard:
    """A guard that protects access to uninitialized session data."""

    def __getattribute__(self, item: str) -> typing.Any:
        if item == "_raise":
            return super().__getattribute__(item)

        self._raise()

    def __setitem__(
        self, key: str, value: typing.Any
    ) -> typing.NoReturn:  # pragma: nocover
        self._raise()

    def __getitem__(self, key: str) -> typing.NoReturn:  # pragma: nocover
        self._raise()

    def _raise(self) -> typing.NoReturn:
        raise SessionNotLoaded(
            "Attempt to access session that has not been loaded yet."
        )


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
