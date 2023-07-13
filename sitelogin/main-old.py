# import asyncio
# import json
# import logging
# import hypercorn
# from hypercorn.typing import HTTPScope, HTTPRequest, HTTPResponse, HTTPVersion
# from hypercorn.typing import ASGIApp, ASGIVersions
import uvicorn
from datetime import datetime
from pydantic import BaseModel, ValidationError
from typing import Union, List, Optional, Annotated
from db.dB import dataBase, queries
from starlette import Form, Depends, FastAPI, HTTPException, Query, Cookie, Body
from starlette.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import jinja2
from jinja2 import Environment, FileSystemLoader
from starlette.requests import Request
from starlette.responses import Response
from starlette.applications import Starlette
from starlette.routing import Route

routes = [
    Route("/", endpoint="index"),
    Route("/login", methods=["GET", "POST"], endpoint="login"),
]
request = Request(scope="http")
response = Response()

# config = hypercorn.config.Config(
#     ASGIVersions = ["2.0"],
#     bind = ["0.0.0.0:8000"],
#     workers = 4,
#     timeout = 60,
#     graceful_timeout = 5,
#     access_log_format = "%(h)s %(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\"",
#     alpn_protocols = ['h2'],
#     log_config = {
#         'version': 1,
#         'formatters': {
#             'default': {
#                 'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
#                 'datefmt': '%Y-%m-%d %H:%M:%S'
# )
# async def app(scope, receive, send):
#     if scope["type"] != "http":
#         raise Exception("Only the HTTP protocol is supported")

#     await send({
#         'type': 'http.response.start',
#         'status': 200,
#         'headers': [
#             (b'content-type', b'text/plain'),
#             (b'content-length', b'5'),
#         ],
#     })
#     await send({
#         'type': 'http.response.body',
#         'body': b'hello',
#     })
#     await send({
#         'type': 'http.response.end',
#     })
#     await send({
#         'type': 'http.disconnect',
#     })

# from quart import Quart, render_template, websocket, url_for, make_push_promise, redirect
# from quart.routing import QuartMap, QuartRule
# from decouple import config
# # import os
# # from quart_auth import Unauthorized
# # from flask import Flask, session
# # from flask_session import MongoDBSessionInterface as mbdsi
# # from flask_session import Session
# import asyncio
# # from hypercorn.asyncio import serve
# from db.dB import dataBase
# import jinja2
# from jinja2 import Environment, FileSystemLoader
# import uvicorn
# from uvicorn import Config

# # loader = FileSystemLoader("templates")
# env = Environment(loader=loader)

# class App:
#     async def __call__(self, scope, receive, send):
#         assert scope['type'] == 'http'


# app = App()

environ = Environment(loader=FileSystemLoader("templates"))


## app.mount("/static", StaticFiles(directory="/nginx/data/static"), name="static")
## pp.mount("/style", StaticFiles(directory="style"), name="style")
templates = Jinja2Templates(directory="templates")


async def app(scope, receive, send):
    assert scope["type"] == "http"
    if scope["type"] != "http":
        raise Exception("Only the HTTP protocol is supported")
    request = Request(scope, receive)
    content = "%s %s %s" % (request.method, request.url.path, request.headers)
    response = Response(content, media_type="text/plain")
    await response(scope, receive, send)


app = Starlette()
db = dataBase.Config("read")


@app.get("/")
async def index(request):
    return HTMLResponse(template_name="index.html")


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.post("/login/")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    dbUsername = dataBase.find("user1", "pass1", "pin1")
    print(dbUsername)
    if dbUsername == username:
        return {"username": username}
    else:
        raise HTTPException(status_code=404, detail="Username not found")


@app.get("/items/", operation_id="some_specific_id_you_define")
async def read_items():
    return [{"item_id": "Foo"}]


if __name__ == "__main__":
    config = uvicorn.Config(
        "main:app", port=8000, log_level="debug", uds="/tmp/fastapi.sock"
    )
    server = uvicorn.Server(config)
    server.run()
