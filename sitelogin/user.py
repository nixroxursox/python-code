import nacl
from nacl import pwhash, utils, encoding
from db.dB import dataBase
from nacl import pwhash, utils, encoding
from pymongo.errors import PyMongoError


class User:
    def __init__(self, *args, **kwargs):
        identifier: int
        username: str
        password: str
        self.id: int
        self.is_admin: bool
        self.user_exists: bool

    def find(self, username):
        """ find existing user by username"""
        rdb = dataBase.Config("read")
        db = rdb["luser"]
        un = username
        try:
            uu = db.find_one({"userId": un})
            if uu:
                return True
            else:
                return False
        except PyMongoError as err:
            return err

    def create(self, *args, **kwargs):
        rdb = dataBase.Config("write")
        db = rdb["luser"]
        un = userId
        pw = password
        pc = pinCode
        nn = nickName
        pgp = pgpKey
        ia = isAdmin
        try:
            if self.find(un) is False:
                result = db.insert_one({}, {"userId": un, "password": pw, "isAdmin": ia,
                                       "pinCode": pc, "nickName": nn, "pgpKey": pgp})
                return result.inserted_id
            else:
                state = "user ID is taken"
                return state
        except PyMongoError as err:
            return err

    def checkPass(self, username, password):
        un = username
        rdb = dataBase.Config("read")
        db = rdb["luser"]
        pp = {}
        pp = db.find_one({"userId": un})
        pw = password
        try:
            cpw = pp["password"]
            print(cpw)
            authenticated = nacl.bindings.crypto_pwhash_scryptsalsa208sha256_str_verify(
                cpw, pw.encode('UTF-8'))
            if authenticated is True:
                return True
            else:
                return False
        except PyMongoError as err:
            return err

    def checkPin(self, username, pin_code):
        un = username
        pin = pin_code
        rdb = dataBase.Config("read")
        db = rdb["luser"]
        pi = {}
        pi = db.find_one({"userId": un})
        pc = pi["pin_code"]
        try:
            if pc is True:
                return pc
        except PyMongoError as err:
            return err

    def isAdmin(self, username):
        rdb = dataBase.Config("read")
        db = rdb["luser"]
        a = {}
        try:
            a = db.find_one({"userId": username})
            if a["isAdmin"] == True:
                return True
            else:
                return False
        except PyMongoError as err:
            return err

    @property
    def is_authenticated(self) -> bool:
        return False

    @property
    def display_name(self) -> str:
        return self.nickName

    @property
    def identity(self) -> int:
        return self.identifier


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
