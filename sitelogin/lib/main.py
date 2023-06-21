# from quart import Quart, render_template, websocket, url_for, make_push_promise, redirect
# from quart.routing import QuartMap, QuartRule
from decouple import config
# import os
# from quart_auth import Unauthorized
# from flask import Flask, session
# from flask_session import MongoDBSessionInterface as mbdsi
# from flask_session import Session
import asyncio
# from hypercorn.asyncio import serve
from db.dB import dataBase
import uvicorn

async def http_server():
    def __call__(self, scope, receive, send):
        assert scope["type"] == "http"
        if scope["type"] != "http" or scope["http_method"]!= "GET":
            async send({"type": "http.response.start", "status": 405, "headers": []})
        return
            async send({"type": "http.response.body", "body": b"Method Not Allowed"})
        return
    return __call__

            


# def create_app():
#     app = Quart(__name__, template_folder="templates")
#     app.secret_key = config("SESS_SECRET_KEY")
#     app.config["SESSION_TYPE"] = "mongodb"
#     app.config["SESSION_PERMANENT"] = False
#     app.config["SESSION_USE_SIGNER"] = True
#     Session(app)
#     return app


# app = create_app()


# @app.route("/")
# async def hello():
#     return await render_template("index.html", context="Hello World")

    
# @app.route("/api")
# async def json():
#     return {"hello": "world"}

# @app.errorhandler(Unauthorized)
# async def redirect_to_login(*_):
#     return redirect(url_for("login"))


# @app.route('/set/')
# def set():
#     session['key'] = 'value'
#     return 'ok'

# @app.route('/get/')
# def get():
#     return session.get('key', 'not set')


# if __name__ == "__main__":
#     asyncio.run(serve(app, config))
    
    
# Bases: object

# access_log_format = '%(h)s %(l)s %(l)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
# accesslog: Optional[Union[Logger, str]] = None
# alpn_protocols = ['h2', 'http/1.1']
# alt_svc_headers: List[str] = []
# application_path: str
# backlog = 100
# property bind: List[str]
# ca_certs: Optional[str] = None
# property cert_reqs
# certfile: Optional[str] = None
# ciphers: str = 'ECDHE+AESGCM'
# create_sockets() → Sockets
# create_ssl_context() → Optional[SSLContext]
# debug = False
# dogstatsd_tags = ''
# errorlog: Optional[Union[Logger, str]] = '-'
# classmethod from_mapping(mapping: Optional[Mapping[str, Any]] = None, **kwargs: Any) → Config
# Create a configuration from a mapping.

# This allows either a mapping to be directly passed or as keyword arguments, for example,

# config = {'keep_alive_timeout': 10}
# Config.from_mapping(config)
# Config.from_mapping(keep_alive_timeout=10)
# Parameters:
# mapping – Optionally a mapping object.
# kwargs – Optionally a collection of keyword arguments to form a mapping.
# classmethod from_object(instance: Union[object, str]) → Config
# Create a configuration from a Python object.

# This can be used to reference modules or objects within modules for example,

# Config.from_object('module')
# Config.from_object('module.instance')
# from module import instance
# Config.from_object(instance)
# are valid.

# Parameters:
# instance – Either a str referencing a python object or the object itself.
# classmethod from_pyfile(filename: Union[AnyStr, PathLike]) → Config
# Create a configuration from a Python file.

# Config.from_pyfile('hypercorn_config.py')
# Parameters:
# filename – The filename which gives the path to the file.
# classmethod from_toml(filename: Union[AnyStr, PathLike]) → Config
# Load the configuration values from a TOML formatted file.

# This allows configuration to be loaded as so

# Config.from_toml('config.toml')
# Parameters:
# filename – The filename which gives the path to the file.
# graceful_timeout: float = 3.0
# group: Optional[int] = None
# h11_max_incomplete_size = 16384
# h2_max_concurrent_streams = 100
# h2_max_header_list_size = 65536
# h2_max_inbound_frame_size = 16384
# include_date_header = True
# include_server_header = True
# property insecure_bind: List[str]
# keep_alive_timeout = 5.0
# keyfile: Optional[str] = None
# keyfile_password: Optional[str] = None
# property log: Logger
# logconfig: Optional[str] = None
# logconfig_dict: Optional[dict] = None
# logger_class
# alias of Logger
# loglevel: str = 'INFO'
# max_app_queue_size: int = 10
# pid_path: Optional[str] = None
# property quic_bind: List[str]
# read_timeout: Optional[int] = None
# response_headers(protocol: str) → List[Tuple[bytes, bytes]]
# property root_path: str
# server_names: List[str] = []
# set_cert_reqs(value: int) → None
# set_statsd_logger_class(statsd_logger: Type[Logger]) → None
# shutdown_timeout = 60.0
# property ssl_enabled: bool
# ssl_handshake_timeout = 60.0
# startup_timeout = 60.0
# statsd_host: Optional[str] = None
# statsd_prefix = ''
# umask: Optional[int] = None#
# use_reloader = False
# user: Optional[int] = None
# verify_flags: Optional[VerifyFlags] = None
# verify_mode: Optional[VerifyMode] = None
# websocket_max_message_size = 16777216
# websocket_ping_interval: Optional[float] = None
# worker_class = 'asyncio'
# workers = 1
# exception hypercorn.config.SocketTypeError(expected: Union[int, SocketKind], actual: Union[int, SocketKind])
# Bases: Exception
# class hypercorn.config.Sockets(secure_sockets: 'List[socket.socket]', insecure_sockets: 'List[socket.socket]', quic_sockets: 'List[socket.socket]')
# Bases: object

# insecure_sockets: List[socket]
# quic_sockets: List[socket]
# secure_sockets: List[socket]
