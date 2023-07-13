import nacl
from nacl import pwhash, utils, encoding
from db.dB import dataBase, queries
from nacl import pwhash, utils, encoding
from pymongo.errors import PyMongoError


class user:
    def __init__() -> None:
        self.userId = None
        self.password = None
        self.pin_code = None

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


class userList:
    def __init__():
        dbUser = None

    def user_loader(username):
        fUser = username
        db = dataBase.Config("read")
        rdb = db["luser"]
        users = rdb.find({"userId": fUser})
        print(fUser)
        return users

    def usersAll():
        db = dataBase.Config("read")
        rdb = db["luser"]
        usersAll = rdb.find({}, {"_id": 0, "userId": 1})
        return usersAll
