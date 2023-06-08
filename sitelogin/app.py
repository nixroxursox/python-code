from quart import Quart, render_template, websocket, url_for, make_push_promise, send_from_directory
from quart.routing import QuartMap, QuartRule
from decouple import config
import os

secret_key = config("SESS_SECRET_KEY")
app = Quart(__name__, static_folder="/static", template_folder="templates")

url_map = QuartMap(
     Rule('/:/style', endpoint='style'),
)

app.url_map.register(url_map)

@app.route("/")
async def hello():

    return await render_template("index.html", context="Hello World")

    
@app.route("/api")
async def json():
    return {"hello": "world"}



if __name__ == "__main__":
    app.run()