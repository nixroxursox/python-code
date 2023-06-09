import pynacl
from pynacl import pwhash, verify, utils, encoding
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
            user = rcol.find_one({"userId": dbDict["userId"]})
            if user is not None:
                if pwhash.verify(dbDict["passwd"], user["passwd"]):
                    return True
                else:
                    return False
        except PyMongoError as e:
            print(e)
            return False
