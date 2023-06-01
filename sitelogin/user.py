from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
from db.dB import dataBase, dbqueries
from nacl import pwhash, utils, encoding


@login_manager.user_loader()




class user():
    def __init__() -> None:
        self.userId = None
        self.passwd = None
        self.pin_code = None

    def checkLogin(userId, passwd, pin_code):
        try:
            dbr = dataBase.Config("read")
            dbc = dbr.readDb("luser")
            lc = dbc.find({}, dbqueries.getUserCreds(userId))
            if userId == lc.userId:
                pwgood == pwhash.verify.str(lc.passwd, passwd)
                pingood = pwhash.verify.str(pin_code, lc.pin_code)
                if pwgood and pingood:
