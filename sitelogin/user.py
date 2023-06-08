
from db.dB import dataBase, queries
from nacl import pwhash, utils, encoding
from pymongo.errors import PyMongoError


class user():
    def __init__() -> None:
        self.userId = None
        self.passwd = None
        self.pinCode = None

    def checkLogin(dbDict):
        try:
            dbr = dataBase.Config("read")
            rcol = dbr["luser"]
            lc = rcol.find_one({},queries.getUserCreds(dbDict[userId]))
            if lc[userId] != None:
                goodpw == pwhash.verify.str(lc[passwd], passwd)
                pingood = pwhash.verify.str(lc[pinCode], fpin_code)
        except PyMongoError as e:
            print(e)
            return False
    