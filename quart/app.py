import quart
import quart_login


app = quart.Quart(__name__)
app.secret_key = 'secret'  # Change this!
login_manager = quart_login.LoginManager()
login_manager.init_app(app)


users = {'foo@bar.tld': {'password': 'secret'}}


class User(quart_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return

    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in users:
        return

    user = User()
    user.id = email
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if quart.request.method == 'GET':
        return '''
               <form action='login' method='POST'>
                <input type='text' name='email' id='email' placeholder='email'/>
                <input type='password' name='password' id='password' placeholder='password'/>
                <input type='submit' name='submit'/>
               </form>
               '''

    email = quart.request.form['email']
    if email in users and quart.request.form['password'] == users[email]['password']:
        user = User()
        user.id = email
        quart_login.login_user(user)
        return quart.redirect(quart.url_for('protected'))

    return 'Bad login'


@app.route('/protected')
@quart_login.login_required
def protected():
    return 'Logged in as: ' + quart_login.current_user.id


@app.route('/logout')
def logout():
    quart_login.logout_user()
    return 'Logged out'


@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized', 401