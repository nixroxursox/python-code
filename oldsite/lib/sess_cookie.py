from quart.sessions import SecureCookieSession, SecureCookieSessionInterface
import app
from decouple import config


async def secure_cookie_session_interface_open_session() -> None:
    session = SecureCookieSession()
    session["siteName"] = "cookie"
    interface = SecureCookieSessionInterface()
    app = Quart(__name__)
    app.secret_key = "secret"
    response = Response("")
    await interface.save_session(app, session, response)
    request = Request(
        "GET", "http", "/", b"", CIMultiDict(), "", "1.1", send_push_promise=no_op_push
    )
    request.headers["Cookie"] = response.headers["Set-Cookie"]
    new_session = await interface.open_session(app, request)
    assert new_session == session
    
    
from contextlib import contextmanager
from http.cookies import SimpleCookie
from sys import version_info
from typing import Generator


from quart.app import Quart
from quart.datastructures import CIMultiDict
from quart.sessions import NullSession, SecureCookieSession, SecureCookieSessionInterface
from quart.testing import no_op_push
from quart.wrappers import Request, Response


@contextmanager
def secure_cookie_session(attribute: str) -> Generator[SecureCookieSession, None, None]:
    session = SecureCookieSession({"a": "b"})
    assert hasattr(session, attribute)
    assert not getattr(session, attribute)
    yield session
    assert getattr(session, attribute)


def secure_cookie_access() -> None:
    with _secure_cookie_session("accessed") as session:
        _ = session["a"]
    with _secure_cookie_session("accessed") as session:
        _ = session.get("a")  # noqa: F841


def secure_cookie_modification() -> None:
    with _secure_cookie_session("modified") as session:
        session.clear()
    with _secure_cookie_session("modified") as session:
        session.setdefault("a", [])
    with _secure_cookie_session("modified") as session:
        session.update({"a": "b"})
    with _secure_cookie_session("modified") as session:
        session["a"] = "b"
    with _secure_cookie_session("modified") as session:
        session.pop("a", None)
    with _secure_cookie_session("modified") as session:
        session.popitem()
    with _secure_cookie_session("modified") as session:
        del session["a"]
    session = SecureCookieSession({"a": "b"})
    _ = session["a"]  # noqa
    assert not session.modified


def null_session_no_modification() -> None:
    session = NullSession()
    with pytest.raises(RuntimeError):
        session.setdefault("a", [])
    with pytest.raises(RuntimeError):
        session.update({"a": "b"})
    with pytest.raises(RuntimeError):
        session["a"] = "b"


@app.mark.asyncio
async def secure_cookie_session_interface_open_session() -> None:
    session = SecureCookieSession()
    session["something"] = "else"
    interface = SecureCookieSessionInterface()
    app = Quart(__name__)
    app.secret_key = "secret"
    response = Response("")
    await interface.save_session(app, session, response)
    request = Request(
        "GET", "http", "/", b"", CIMultiDict(), "", "1.1", send_push_promise=no_op_push
    )
    request.headers["Cookie"] = response.headers["Set-Cookie"]
    new_session = await interface.open_session(app, request)
    assert new_session == session


@mark.asyncio
async def secure_cookie_session_interface_save_session() -> None:
    session = SecureCookieSession()
    session["something"] = "else"
    interface = SecureCookieSessionInterface()
    app = Quart(__name__)
    app.secret_key = "secret"
    response = Response("")
    await interface.save_session(app, session, response)
    cookies: SimpleCookie = SimpleCookie()
    cookies.load(response.headers["Set-Cookie"])
    cookie = cookies[app.session_cookie_name]
    assert cookie["path"] == interface.get_cookie_path(app)
    assert cookie["httponly"] == "" if not interface.get_cookie_httponly(app) else True
    assert cookie["secure"] == "" if not interface.get_cookie_secure(app) else True
    if version_info >= (3, 8):
        assert cookie["samesite"] == (interface.get_cookie_samesite(app) or "")
    assert cookie["domain"] == (interface.get_cookie_domain(app) or "")
    assert cookie["expires"] == (interface.get_expiration_time(app, session) or "")
    assert response.headers["Vary"] == "Cookie"



async def _save_session(session: SecureCookieSession) -> Response:
    interface = SecureCookieSessionInterface()
    app = Quart(__name__)
    app.secret_key = "secret"
    response = Response("")
    await interface.save_session(app, session, response)
    return response



async def secure_cookie_session_interface_save_session_no_modification() -> None:
    session = SecureCookieSession()
    session["something"] = "else"
    session.modified = False
    response = await _save_session(session)
    assert response.headers.get("Set-Cookie") is None



async def secure_cookie_session_interface_save_session_no_access() -> None:
    session = SecureCookieSession()
    session["something"] = "else"
    session.accessed = False
    session.modified = False
    response = await _save_session(session)
    assert response.headers.get("Set-Cookie") is None
    assert response.headers.get("Vary") is None

---------------------------------------------------------------------------------------------

import hashlib
from collections.abc import MutableMapping
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional, TYPE_CHECKING

from itsdangerous import BadSignature, URLSafeTimedSerializer

from .json.tag import TaggedJSONSerializer
from .wrappers import BaseRequestWebsocket, Response

if TYPE_CHECKING:
    from .app import Quart  # noqa


class SessionMixin:
    """Use to extend a dict with Session attributes.

    The attributes add standard and expected Session modification flags.

    Attributes:
        accessed: Indicates if the Session has been accessed during
            the request, thereby allowing the Vary: Cookie header.
        modified: Indicates if the Session has been modified during
            the request handling.
        new: Indicates if the Session is new.
    """

    accessed = True
    modified = True
    new = False

    @property
    def permanent(self) -> bool:
        return self.get("_permanent", False)  # type: ignore

    @permanent.setter
    def permanent(self, value: bool) -> None:
        self["_permanent"] = value  # type: ignore


def _wrap_modified(method: Callable) -> Callable:
    @wraps(method)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        self.accessed = True
        self.modified = True
        return method(self, *args, **kwargs)

    return wrapper


def _wrap_accessed(method: Callable) -> Callable:
    @wraps(method)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        self.accessed = True
        return method(self, *args, **kwargs)

    return wrapper


class Session(MutableMapping):
    """An abstract base class for Sessions."""

    pass


class SecureCookieSession(SessionMixin, dict, Session):
    """A session implementation using cookies.

    Note that the intention is for this session to use cookies, this
    class does not implement anything bar modification and accessed
    flags.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.accessed = False
        self.modified = False

    __delitem__ = _wrap_modified(dict.__delitem__)
    __getitem__ = _wrap_accessed(dict.__getitem__)
    __setitem__ = _wrap_modified(dict.__setitem__)
    clear = _wrap_modified(dict.clear)
    get = _wrap_accessed(dict.get)
    pop = _wrap_modified(dict.pop)
    popitem = _wrap_modified(dict.popitem)
    setdefault = _wrap_modified(dict.setdefault)
    update = _wrap_modified(dict.update)


def _wrap_no_modification(method: Callable) -> Callable:
    @wraps(method)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("Cannot create session, ensure there is a app secret key.")

    return wrapper


class NullSession(Session, dict):
    """A session implementation for sessions without storage."""

    __delitem__ = _wrap_no_modification(dict.__delitem__)
    __setitem__ = _wrap_no_modification(dict.__setitem__)
    clear = _wrap_no_modification(dict.clear)
    pop = _wrap_no_modification(dict.pop)
    popitem = _wrap_no_modification(dict.popitem)
    setdefault = _wrap_no_modification(dict.setdefault)
    update = _wrap_no_modification(dict.update)


class SessionInterface:
    """Base class for session interfaces.

    Attributes:
        null_session_class: Storage class for null (no storage)
            sessions.
        pickle_based: Indicates if pickling is used for the session.
    """

    null_session_class = NullSession
    pickle_based = False

    async def make_null_session(self, app: "Quart") -> NullSession:
        """Create a Null session object.

        This is used in replacement of an actual session if sessions
        are not configured or active.
        """
        return self.null_session_class()

    def is_null_session(self, instance: object) -> bool:
        """Returns True is the instance is a null session."""
        return isinstance(instance, self.null_session_class)

    def get_cookie_domain(self, app: "Quart") -> Optional[str]:
        """Helper method to return the Cookie Domain for the App."""
        if app.config["SESSION_COOKIE_DOMAIN"] is not None:
            return app.config["SESSION_COOKIE_DOMAIN"]
        elif app.config["SERVER_NAME"] is not None:
            return "." + app.config["SERVER_NAME"].rsplit(":", 1)[0]
        else:
            return None

    def get_cookie_path(self, app: "Quart") -> str:
        """Helper method to return the Cookie path for the App."""
        return app.config["SESSION_COOKIE_PATH"] or app.config["APPLICATION_ROOT"] or "/"

    def get_cookie_httponly(self, app: "Quart") -> bool:
        """Helper method to return if the Cookie should be HTTPOnly for the App."""
        return app.config["SESSION_COOKIE_HTTPONLY"]

    def get_cookie_secure(self, app: "Quart") -> bool:
        """Helper method to return if the Cookie should be Secure for the App."""
        return app.config["SESSION_COOKIE_SECURE"]

    def get_cookie_samesite(self, app: "Quart") -> str:
        """Helper method to return the Cookie Samesite configuration for the App."""
        return app.config["SESSION_COOKIE_SAMESITE"]

    def get_expiration_time(self, app: "Quart", session: SessionMixin) -> Optional[datetime]:
        """Helper method to return the Session expiration time.

        If the session is not 'permanent' it will expire as and when
        the browser stops accessing the app.
        """
        if session.permanent:
            return datetime.utcnow() + app.permanent_session_lifetime
        else:
            return None

    def should_set_cookie(self, app: "Quart", session: SessionMixin) -> bool:
        """Helper method to return if the Set Cookie header should be present.

        This triggers if the session is marked as modified or the app
        is configured to always refresh the cookie.
        """
        if session.modified:
            return True
        save_each = app.config["SESSION_REFRESH_EACH_REQUEST"]
        return save_each and session.permanent

    async def open_session(self, app: "Quart", request: BaseRequestWebsocket) -> Optional[Session]:
        """Open an existing session from the request or create one.

        Returns:
            The Session object or None if no session can be created,
            in which case the :attr:`null_session_class` is expected
            to be used.
        """
        raise NotImplementedError()

    async def save_session(self, app: "Quart", session: Session, response: Response) -> Response:
        """Save the session argument to the response.

        Returns:
            The modified response, with the session stored.
        """
        raise NotImplementedError()


class SecureCookieSessionInterface(SessionInterface):
    """A Session interface that uses cookies as storage.

    This will store the data on the cookie in plain text, but with a
    signature to prevent modification.
    """

    digest_method = staticmethod(hashlib.sha1)
    key_derivation = "hmac"
    salt = "cookie-session"
    serializer = TaggedJSONSerializer()
    session_class = SecureCookieSession

    def get_signing_serializer(self, app: "Quart") -> Optional[URLSafeTimedSerializer]:
        """Return a serializer for the session that also signs data.

        This will return None if the app is not configured for secrets.
        """
        if not app.secret_key:
            return None

        options = {"key_derivation": self.key_derivation, "digest_method": self.digest_method}
        return URLSafeTimedSerializer(
            app.secret_key, salt=self.salt, serializer=self.serializer, signer_kwargs=options
        )

    async def open_session(
        self, app: "Quart", request: BaseRequestWebsocket
    ) -> Optional[SecureCookieSession]:
        """Open a secure cookie based session.

        This will return None if a signing serializer is not availabe,
        usually if the config SECRET_KEY is not set.
        """
        signer = self.get_signing_serializer(app)
        if signer is None:
            return None

        cookie = request.cookies.get(app.session_cookie_name)
        if cookie is None:
            return self.session_class()
        try:
            data = signer.loads(cookie, max_age=app.permanent_session_lifetime.total_seconds())
            return self.session_class(**data)
        except BadSignature:
            return self.session_class()

    async def save_session(  # type: ignore
        self, app: "Quart", session: SecureCookieSession, response: Response
    ) -> None:
        """Saves the session to the response in a secure cookie."""
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        if not session:
            if session.modified:
                response.delete_cookie(app.session_cookie_name, domain=domain, path=path)
            return

        if session.accessed:
            response.vary.add("Cookie")

        if not self.should_set_cookie(app, session):
            return

        data = self.get_signing_serializer(app).dumps(dict(session))
        response.set_cookie(
            app.session_cookie_name,
            data,
            expires=self.get_expiration_time(app, session),
            httponly=self.get_cookie_httponly(app),
            domain=domain,
            path=path,
            secure=self.get_cookie_secure(app),
            samesite=self.get_cookie_samesite(app),
        )