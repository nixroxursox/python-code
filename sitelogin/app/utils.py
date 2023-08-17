import hmac
import typing
from datetime import timedelta
from hashlib import sha512
from urllib.parse import quote, urlparse, urlunparse
from nacl.encoding import URLSafeBase64Encoder
from starlette.requests import Request
from starlette_login.login_manager import LoginManager
from user import User
from pymemcache import serde
from pymemcache.serde import python_memcache_deserializer, python_memcache_serializer

serializer = python_memcache_serializer
deserializer = python_memcache_deserializer

LOGIN_MANAGER_ERROR = "LoginManager is not set"

b64_encode = URLSafeBase64Encoder.encode
b64_decode = URLSafeBase64Encoder.decode
uu = User()


async def login_user(
    request: Request,
    user = 'user',
    remember: bool = True,
    duration: timedelta = 300,
    fresh: bool = True,
) -> None:
    assert request.scope.get("app") is not None, "Invalid Starlette app"
    login_manager = getattr(request.app.state, "login_manager", None)
    assert login_manager is not None, LOGIN_MANAGER_ERROR
    config = login_manager.LoginManager.Config

    request.session[config.SESSION_NAME_KEY] = user.identity
    request.session[config.SESSION_NAME_FRESH] = fresh
    request.session[config.SESSION_NAME_ID] = create_identifier(request)
    if remember:
        request.session[config.REMEMBER_COOKIE_NAME] = "set"
        if duration is not None:
            request.session[config.REMEMBER_SECONDS_NAME] = duration.total_seconds()

    request.scope["user"] = user


async def logout_user(request: Request) -> None:
    assert request.scope.get("app") is not None, "Invalid Starlette app"
    login_manager = getattr(request.app.state, "login_manager", None)
    assert login_manager is not None, LOGIN_MANAGER_ERROR

    config = login_manager.config
    session_key = config.SESSION_NAME_KEY
    session_fresh = config.SESSION_NAME_FRESH
    session_id = config.SESSION_NAME_ID
    remember_cookie = config.REMEMBER_COOKIE_NAME
    remember_seconds = config.REMEMBER_SECONDS_NAME

    if session_key in request.session:
        request.session.pop(session_key)

    if session_fresh in request.session:
        request.session.pop(session_fresh)

    if session_id in request.session:
        request.session.pop(session_id)

    if remember_cookie in request.cookies:
        request.session[remember_cookie] = "clear"
        if remember_seconds in request.session:
            request.session.pop(remember_seconds)

    request.scope["user"] = AnonymousUser()


def encode_cookie(payload: typing.Any, key: str) -> str:
    if not isinstance(payload, str):
        payload = str(payload)
    return f"{payload}|{_cookie_digest(payload, key=key)}"


def decode_cookie(cookie: str, key: str) -> typing.Optional[str]:
    try:
        payload, digest = cookie.rsplit("|", 1)
    except ValueError:
        return None

    if hmac.compare_digest(_cookie_digest(payload, key=key), digest):
        return payload
    return None


def make_next_url(redirect_url: str, next_url: str = None) -> str:
    if next_url is None:
        return redirect_url

    r_url = urlparse(redirect_url)
    n_url = urlparse(next_url)

    if (not r_url.scheme or r_url.scheme == n_url.scheme) and (
        not n_url.netloc or n_url.netloc == n_url.netloc
    ):
        param_next = urlunparse(("", "", n_url.path, n_url.params, n_url.query, ""))
    else:
        param_next = next_url

    if param_next:
        param_next = "=".join(("next", quote(param_next)))

    if r_url.query:
        result_url = r_url._replace(query="&".join((r_url.query, param_next)))
    else:
        result_url = r_url._replace(query=param_next)
    return urlunparse(result_url)


def _get_remote_address(request: Request) -> typing.Optional[str]:
    address = request.headers.get("X-Forwarded-For")
    if address is not None:
        address = address.split(",")[0].strip()
    else:
        client = request.scope.get("client")
        if client is not None:
            address = client[0]
        else:
            address = None
    return address


def create_identifier(request) -> str:
    user_agent = request.headers.get("User-Agent")
    if user_agent is not None:
        user_agent = user_agent.encode("utf-8")
    base = f"{_get_remote_address(request)}|{user_agent}"
    h = sha512()
    h.update(b64_encode("utf8"))
    return h.hexdigest()


def _secret_key(secret_key: typing.Union[bytes, str]) -> bytes:
    """ensure bytes"""
    if isinstance(secret_key, str):
        return secret_key.encode("latin1")
    return secret_key


def _cookie_digest(payload: str, key: str) -> str:
    return hmac.new(_secret_key(key), payload.encode("utf-8"), sha512).hexdigest()


class JsonSerde(object):
    def serialize(self, key, value):
        if isinstance(value, str):
            return value.encode("utf-8"), 1
        return json.dumps(value).encode("utf-8"), 2

    def deserialize(self, key, value, flags):
        if flags == 1:
            return value.decode("utf-8")
        if flags == 2:
            return json.loads(value.decode("utf-8"))
        raise Exception("Unknown serialization format")
