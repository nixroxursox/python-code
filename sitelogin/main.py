from quart import Quart, render_template, websocket, url_for, make_push_promise, redirect
from quart.routing import QuartMap, QuartRule
from decouple import config
import os
from quart_auth import Unauthorized
from flask import Flask, session
from flask_session import Session



secret_key = config("SESS_SECRET_KEY")
app = Quart(__name__, template_folder="templates")


@app.route("/")
async def hello():
    return await render_template("index.html", context="Hello World")

    
@app.route("/api")
async def json():
    return {"hello": "world"}

@app.errorhandler(Unauthorized)
async def redirect_to_login(*_):
    return redirect(url_for("login"))


app = Flask(__name__)
# Check Configuration section for more details
SESSION_TYPE = 'redis'
app.config.from_object(__name__)
Session(app)

@app.route('/set/')
def set():
    session['key'] = 'value'
    return 'ok'

@app.route('/get/')
def get():
    return session.get('key', 'not set')


if __name__ == "__main__":
    app.run()