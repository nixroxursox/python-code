from db.dB import dataBase
import quart
from quart import Quart
from nacl import utils
import quart_login



db = dataBase.readDb("locker", "luser")

app = quart.Quart(__name__)
app.secret_key = utils.random(12)  # Change this!
login_manager = quart_login.LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.init_app(app)
from user import user
r

@app.route('/login', methods=['GET', 'POST'])
def login():
    if quart.request.method == 'GET':
        return '''
               <form action='login' method='POST'>
                <input type='text' name='userId' id='userId' placeholder='userId'/>
                <input type='password' name='password' id='password' placeholder='password'/>
                <input type='submit' name='submit'/>
               </form>
               '''

    userId = quart.request.form['userId']
    if userId in users and quart.request.form['password'] == users[userId]['password']:
        user = user()
        userId = userId
        quart_login.login_user(user)
        return quart.redirect(quart.url_for('protected'))

    return 'Bad login'


@app.route('/protected')
@quart_login.login_required
def protected():
    return 'Logged in as: ' + quart_login.current_user.userId


if __name__ == '__main__':
    app.run(debug=True)