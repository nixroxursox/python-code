from flask_login import LoginManager
from db.dB import dataBase, 
from sitelogin.db import notused
from nacl import pwhash, utils, encoding




login_manager = LoginManager()
login_manager.init_app(app=app)

@login_manager.user_loader()




class user():
    def __init__() -> None:
        self.userId = None
        self.passwd = None
        self.pin_code = None

    def checkLogin(dbDict):
        try:
            dbr = dataBase.Config("read")
            rcol = dbr["luser"]
            lc = rcol.find_one({}, notused.getUserCreds(dbDict[userId]))
            if lc[userId] != None:
                goodpw == pwhash.verify.str(lc[passwd], passwd)
                pingood = pwhash.verify.str(lc[pinCode], fpin_code)
                if goodpw == True:
                    if pingood == True
            return True
        except pymongoerror as e:
            return false