# quart_auth.LoginManager(app)
# login_manager.login_view = "login"
# login_manager.login_message_category = "info"
# loginUserMixin):
from db import dB

class user():
    def __init__(self, userId, passwd, pin_code):
        self.userId = chkUser
        self.passwd = passwd
        self.pin_code = pin_code

    def getUid(self, chkUser, pwd):
        db = dataBase.readDb("locker", "luser")
        if db is None:
            return None
        for doc in db.find({"userId": userId, "passwd": pwd}):
            return doc["_id"]

# @login_manager.user_loader
def user_loader(userId):
    if userId not in user:
        return

    user = user()
    userId = self.userId()
    return user

# @login_manager.request_loader
def request_loader(request):
    userId = request.form.get('userId')
    passwd = request.form.get('passwd')
    pin_code = request.form.get('pin_code')
    if userId not in users:
        return

    user = user()
    userId = self.userId()
    return user