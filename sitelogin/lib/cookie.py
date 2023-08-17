import nacl
from nacl import pwhash, encoding, secret
from decouple import config
from flask_mongo_sessions import MongoDBSessionInterface, SessionMixin, uuid, CallbackDict, pickle
import os
from starlette.applications import Request, Response
#from cache import Cache
from middleware import Serializer
from middleware.Serializer import serialize, deserialize

secret_key = config("B_SESS_SECRET_KEY")

def SessionInterface(): pass


serialize = Serializer.serialize()
deserialize = Serializer.deserialize()

def client_session(self):
    data = self.cookies.get("session_data")
    if not data:
        return SecureCookie(secret_key)
    return SecureCookie.unserialize(data, secret_key)


def application(environ, start_response):
    request = Request(environ)

    # get a response object here
    response = ...

    if request.client_session.should_save:
        session_data = request.client_session.serialize()
=         response.set_cookie("session_data", session_data, httponly=True)
        return response(environ, start_response)


class SessionData(dict, SessionMixin):
    pass


class Session():
    session_class = SessionData

    def open_session(self, app, request):
        self.cookie_session_id = request.cookies.get(app.session_cookie_name, type=str)
        self.session_new = False
        if self.cookie_session_id is None:
            self.cookie_session_id = os.urandom(40).encode("hex")
            self.session_new = True
        self.memcache_session_id = "@".join(
            [request.remote_addr, self.cookie_session_id]
        )
        app.logger.debug("Open session %s", self.memcache_session_id)
        session = app.cache.get(self.memcache_session_id) or {}
        app.cache.set(self.memcache_session_id, session)
        return self.session_class(session)

    def save_session(self, app, session, response):
        expires = self.get_expiration_time(app, session)
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        app.cache.set(self.memcache_session_id, session)
        if self.session_new:
            response.set_cookie(
                app.session_cookie_name,
                self.cookie_session_id,
                path=path,
                expires=expires,
                httponly=httponly,
                secure=secure,
                domain=domain,
            )
            app.logger.debug(
                "Set session %s with %s", self.memcache_session_id, session
            )


async def secure_cookie_session_interface_open_session() -> None:
    session = SecureCookieSession()
    session["something"] = "else"
    interface = SecureCookieSessionInterface()
    response = Response("")
    await interface.save_session(app, session, response)
    request = Request(
        "GET", "http", "/", b"", CIMultiDict(), "", "1.1", send_push_promise=no_op_push
    )
    request.headers["Cookie"] = response.headers["Set-Cookie"]
    new_session = await interface.open_session(app, request)
    assert new_session == session
