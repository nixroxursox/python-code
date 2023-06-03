import quart 
##    from quart.templating import Environment, render_template, get_template
from quart import Quart, render_template, g, request, make_response
import jinja2
from jinja2 import Environment, Template
from jinja2.loaders import FileSystemLoader
#from jinja2.loaders import DictLoader
from flask_login import LoginManager, login_required, current_user
from flask import session
from db.dB import dataBase, queries
from flask_login import LoginManager, config
import uuid


login_manager = LoginManager()
login_manager.login_view = 'auth.login'


config_name = "prod"


def create_app(config_name):
    """ Server app related configuration
    """
    app = Quart(__name__, static_folder="static", template_folder="templates")
    ## app.config.from_object(config[config_name])
    ## config[config_name].init_app(app=app)
    app.secret_key = uuid.uuid1().__str__()
    app.jinja_env.variable_start_string = "[["
    app.jinja_env.variable_end_string = "]]"
    ## cache = Cache(config={"CACHE_TYPE": "simple"})

    appDb = dataBase.Config("read")
    # mail.init_app(app=app)
    #cache.init_app(app=app)
    login_manager.init_app(app=app)
    #socket_io.init_app(app=app)

    #from app.view import views
    #from dialogue.pytorch.apis import apis
    #app.register_blueprint(views)

    return app
# env = Environment(loader=DictLoader({
# 'a': '''[A[{% block body %}{% endblock %}]]''',
# 'b': '''{% extends 'a' %}{% block body %}[B]{% endblock %}''',
# 'c': '''{% extends 'b' %}{% block body %}###{{ super() }}###{% endblock %}'''
# }))
# methods = 'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'
# scheme  = 'http'
# headers = [
#     ('Access-Control-Allow-Origin', '*'),
#     ('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS'),
#     ('Access-Control-Allow-Headers', 'Content-Type, Authorization, Content-Length, X-Requested-With'),
#     ('Access-Control-Allow-Credentials', 'true'),
#     ('Content-Type', 'text/html; charset=utf-8')
#     ('X-real-ip', '127.0.0.1')
# ]
# http_version = '1.1'
# assert scope(request, response) == 'http'
# assert request.method in methods
app = create_app("prod")

@app.route('/')
def index():
    if 'username' in session:
        return f'Logged in as {session["username"]}'
    return 'You are not logged in'


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))


# print(env.get_template('c').render())

# from jinja2 import Environment
# from jinja2.loaders import FileSystemLoader


# #template = Template(directory="templates")
# async def do_the_login():    
#     response = await make_response("Hello")
#     response.set_cookie("cooookie", "1")
#     return response


# async def show_the_login():
#     request.method
#     request.url
#     request.headers["X-Bob"]
#     request.args.get("a")  # Query string e.g. example.com/hello?a=2
#     await request.get_data()  # Full raw body
#     (await request.form)["name"]
#     (await request.get_json())["key"]
#     request.cookies.get("name")

    
#     return await render_template('auth/login.html')
# return await render_template('auth/login.html')
# tmpl = env.get_template('index.html')
# tmp2 = template.render_async("index.html", context="hello world")
# # print tmpl.render(seq=[3, 2, 4, 5, 3, 2, 0, 2, 1])
# print(tmp2)

# ##  template = ("templates")
# ## message = get_template("message.txt")


@app.post("/login")
@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        if valid_login(request.form['username'],
                       request.form['password']):
            return log_the_user_in(request.form['username'])
        else:
            error = 'Invalid username/password'
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return render_template('auth/login.html', error=error)


@app.route("/", methods=["GET"])
async def index():
    return 'hello'



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
