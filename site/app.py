import hypercorn
import asyncio
import exceptions
# import user
from quart import redirect, url_for, render_template, flash, request, session, jsonify, redirect, url_for
from quart.app import Quart
from quart_auth import (
    AuthUser, AuthManager, current_user, login_required, login_user, logout_user, Unauthorized
)
from nacl import pwhash, utils, encoding
import os
import quart_session
from quart_session import Session
from decouple import config
from db.dB import dataBase
import jinja2
from jinja2 import Environment, FileSystemLoader


# class errorhandler():
#     pass



# # config = Quart.config_class(
# #     static_folder = "static",
# #     template_folder = "templates",
# #     debug = True,
# #     root_path = os.path.dirname(os.path.abspath(__file__))
# # )
app = Quart(__name__)

sess = Session()
auth_manager = AuthManager(app)


        
#app.auth_manager.init_app(app)
app.secret_key = config('SECRET_KEY')
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = {
    'host': config('REDIS_HOST'),
    'port': config('REDIS_PORT'),
    'rdb': config('REDIS_DB')
}
app.config['SESSION_FILE_DIR'] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),'sessions')
app.config['SESSION_FILE_TIMEOUT'] = 86400
app.config['SESSION_FILE_SECURE'] = False
app.config['SESSION_FILE_HTTPONLY'] = True
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_NAME'] ='session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# app.session_cookie_name = "sessionId"
app.create_jinja_environment()


environment = Environment(loader=FileSystemLoader("templates"))
template = environment.get_template("message.txt")


@app.route("/login", methods=['GET', 'POST'])
async def login():
    if await current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == 'POST':
        def get_form_data():
            return {
                'username': request.form.get('username'),
                'password': request.form.get('password'),
                'pin_code': request.form.get('pin_code')
            }



    dbDict = {}
    fuserId = 'username'
    fpasswd = 'password'
    fpin_code = 'pin_code'
    dbDict = ("locker","luser",fuserId, fpasswd, fpin_code)
    usrChk = dataBase.find(dbDict)
    if usrChk == True:
        pass
            
#             login_user(user)
#             return redirect(url_for("index"))
#         else:
#             return render_template("auth/login.html", error="Invalid Credentials")
#     return render_template("auth/login.html")

# # @app.route("/logout")
# # @login_required
#     # We'll assume the user has an identifying ID equal to 2login_user(AuthUser(2))    ...
#     # @app.route("/logout")
# async def logout():
#     logout_user()
#     """_summary_
#     Returns:
#         _type_: _description_
#     """

@app.route("/")
async def index():
    return render_template("index.html")
    #return render_template("auth/login.html")
#async def restricted_route():
#current_user.auth_id  # Will be 2 given the login_user code above


# @app.route("/hello")
# async def hello():
#     return await render_template_string("""
#     {% if current_user.is_authenticated %}
#       Hello logged in user
#     {% else %}
#       Hello logged out user
#     {% endif %}
#     """)


@app.errorhandler(Unauthorized)
async def redirect_to_login(*_):
    return redirect(url_for("login"))



# @app.websocket("/ws")
# @login_required
# async def ws():
#     await websocket.send(f"Hello {current_user.auth_id}")

    
if __name__ == "__main__":
    app.run(host='0.0.0.0')
    sess(app)
    