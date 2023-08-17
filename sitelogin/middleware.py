import typing as t

from starlette.middleware.base import BaseHTTPMiddleware

from backends import BaseAuthenticationBackend, SessionAuthBackend, ModelAuthBackend
from login_manager import LoginManager
from starsessions import Serializer, SessionStore, InMemoryStore
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

from starsessions import SessionNotLoaded
from starsessions.serializers import JsonSerializer, Serializer
from starsessions.session import SessionHandler, get_session_remaining_seconds, load_session
from starsessions.stores import SessionStore, InMemoryStore, CookieStore


b64_encode = URLSafeBase64Encoder.encode
b64_decode = URLSafeBase64Encoder.decode

sk = config("SECRET_KEY")

class AuthenticationMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        backend: ModelAuthBackend,
        login_manager: LoginManager,
        excluded_dirs: t.List[str] = None,
        allow_websocket: bool = False
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


class Serializer(Serializer):
    def serialize(self, data: t.Any) -> bytes:
        return json.dumps(data).encode("utf-8")

    def deserialize(self, data: bytes) -> t.Dict[str, t.Any]:
        return json.loads(data)



class LoadGuard:
    """A guard that protects access to uninitialized session data."""

    def __getattribute__(self, item: str) -> typing.Any:
        if item == "_raise":
            return super().__getattribute__(item)

        self._raise()

    def __setitem__(self, key: str, value: typing.Any) -> typing.NoReturn:  # pragma: nocover
        self._raise()

    def __getitem__(self, key: str) -> typing.NoReturn:  # pragma: nocover
        self._raise()

    def _raise(self) -> typing.NoReturn:
        raise SessionNotLoaded("Attempt to access session that has not been loaded yet.")


class SessionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        store: SessionStore,
        lifetime: typing.Union[int, datetime.timedelta] = 0,  # session-only
        rolling: bool = False,
        cookie_name: str = "session_",
        cookie_same_site: str = "lax",
        cookie_https_only: bool = False,
        cookie_domain: typing.Optional[str] = None,
        cookie_path: typing.Optional[str] = None,
        serializer: typing.Optional[Serializer] = None,
    ) -> None:
        lifetime = int(lifetime.total_seconds() if isinstance(lifetime, datetime.timedelta) else lifetime)
        assert lifetime >= 0, "Session lifetime cannot be less than zero seconds."

        self.app = app
        self.store = store
        self.rolling = rolling
        self.serializer = serializer or JsonSerializer()
        self.cookie_name = cookie_name
        self.lifetime = lifetime
        self.cookie_domain = cookie_domain
        self.cookie_path = cookie_path
        self.security_flags = "httponly; samesite=" + cookie_same_site
        if cookie_https_only:  # Secure flag can be used with HTTPS only
            self.security_flags += "; secure"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        session_id = connection.cookies.get(self.cookie_name)
        handler = SessionHandler(connection, session_id, self.store, self.serializer, self.lifetime)

        scope["session"] = LoadGuard()
        scope["session_handler"] = handler

        async def send_wrapper(message: Message) -> None:
            if message["type"] != "http.response.start":
                await send(message)
                return

            # session was not loaded, do nothing
            if not handler.is_loaded:  # pragma: nocover
                await send(message)
                return

            nonlocal session_id
            path = self.cookie_path or scope.get("root_path", "") or "/"

            if handler.is_empty:
                # if session was initially empty then do nothing
                if handler.initially_empty:
                    await send(message)
                    return

                # session data loaded but empty, no matter whether it was initially empty or cleared
                # we have to remove the cookie and clear the storage
                if not self.cookie_path or self.cookie_path and scope["path"].startswith(self.cookie_path):
                    headers = MutableHeaders(scope=message)
                    header_value = "{}={}; {}".format(
                        self.cookie_name,
                        f"null; path={path}; expires=Thu, 01 Jan 1970 00:00:00 GMT;",
                        self.security_flags,
                    )
                    headers.append("Set-Cookie", header_value)
                    await handler.destroy()
                await send(message)
                return

            # calculate cookie/storage expiry seconds based on selected strategy
            remaining_time = 0

            # if lifetime is zero then don't send max-age at all
            # this will create session-only cookie
            if self.lifetime > 0:
                if self.rolling:
                    # rolling strategy always extends cookie max-age by lifetime
                    remaining_time = self.lifetime
                else:
                    # non-rolling strategy reuses initial expiration date
                    remaining_time = get_session_remaining_seconds(connection)

            # persist session data
            session_id = await handler.save(remaining_time)

            headers = MutableHeaders(scope=message)
            header_parts = [
                f"{self.cookie_name}={session_id}",
                f"path={path}",
            ]

            if self.lifetime > 0:  # always send max-age for non-session scoped cookie
                header_parts.append(f"max-age={remaining_time}")

            if self.cookie_domain:
                header_parts.append(f"domain={self.cookie_domain}")

            header_parts.append(self.security_flags)
            header_value = "; ".join(header_parts)
            headers.append("set-cookie", header_value)

            await send(message)

        await self.app(scope, receive, send_wrapper)


class SessionAutoloadMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        paths: typing.Optional[typing.List[typing.Union[str, typing.Pattern[str]]]] = None,
    ) -> None:
        self.app = app
        self.paths = paths or []

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope, receive)
        if self.should_autoload(connection):
            await load_session(connection)

        await self.app(scope, receive, send)

    def should_autoload(self, connection: HTTPConnection) -> bool:
        if not self.paths:
            return True

        for path in self.paths:
            if re.match(path, connection.url.path):
                return True
        return False