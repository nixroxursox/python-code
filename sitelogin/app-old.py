from flask_login import LoginManager, login_user, logout_user, current_user, login_required
import quart
import asyncio
from typing import Optional

from quart import Response, Quart, Session, render_template, request, session, ASGIHTTPConnection, Response
import nacl
from nacl import pwhash, encoding, utils
from decouple import config
secret_key = config("SESS_SECRET_KEY")
#import cache
#import middleware
#import user
#import register



#Sdef http_1_1_host_header(headers: list, expected: str) -> None:
 

def create_app():
    app = Quart(__name__, static_folder = "static", template_folder = "templates")
    request = connection._create_request_from_scope(lambda: None)
    assert request.headers["host"] == "expected" 
    app.config["SESSION_PERMANENT"] = False
    #app.config["SESSION_TYPE"] = "memcached"
    app.config['SECRET_KEY'] = secret_key
    login_manager = LoginManager() 
    login_manager.init_app(app=app)
    app.clients = set()
    Session(app)
    return app

scope = {
    "headers": "headers",
    "http_version": "1.1",
    "method": "GET",
    "scheme": "http",
    "path": "/",
    "query_string": b"",
}


app = create_app()
connection = ASGIHTTPConnection(app, scope)
app.clients.add(connection)




class ServerSentEvent:

    def __init__(
            self,
            data: str,
            *,
            event: Optional[str]=None,
            id: Optional[int]=None,
            retry: Optional[int]=None,
    ) -> None:
        self.data = data    
        request = connection._create_request_from_scope(lambda: None)
        self.event = event
        self.id = id
        self.retry = retry

    def encode(self) -> bytes:
        message = f"data: {self.data}"
        if self.event is not None:
            message = f"{message}\nevent: {self.event}"
        if self.id is not None:
            message = f"{message}\nid: {self.id}"
        if self.retry is not None:
            message = f"{message}\nretry: {self.retry}"
        message = f"{message}\r\n\r\n"
        return message.encode('utf-8')



@app.route('/', methods=['GET'])
async def index():
    response = await client.get("/")
    secure_cookie_session_interface_open_session()
    return await render_template('index.html')


@app.route('/', methods=['POST'])
async def broadcast():
    data = await request.get(await quart.formData('fuserId'))
    for queue in app.clients:
        await queue.put(data['message'])
    return jsonify(True)
 

 
@app.route("/logout")
def logout():
    session["name"] = None
    return redirect("/")
 

# -*- coding: utf-8 -*-
"""
    Hello
    ~~~~~

    Quart-Session demo.

    :copyright: (c) 2020 by Kroket Ltd.
    :license: BSD, see LICENSE for more details.
"""



SESSION_TYPE = 'redis'


@app.route('/set/')
async def set():
    session['key'] = 'value'
    return 'ok'


@app.route('/get/')
async def get():
    return session.get('key', 'not set')


if __name__ == "__main__":
    app.run(debug=True)
