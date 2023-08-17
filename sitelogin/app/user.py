import typing
from dataclasses import dataclass
from datetime import datetime, timezone
import pymongo
import nacl
from nacl import encoding, pwhash, utils
from starlette.applications import Starlette
from pymongo.errors import PyMongoError
from starlette.requests import Request, HTTPConnection
from db.dB import dataBase, q


class User:
    """user class for authentication"""

    def __init__(self, *args, **kwargs):
        self.masterId: int
        self.userName: str
        self.password: str
        self.nickName: str
        self.isAdmin: bool
        self.user_exists: bool

    def find(self, userName, *args, **kwargs) -> False:
        """find existing user by userName"""
        rdb = dataBase.conf("read")
        db = rdb["userLogins"]
        un = userName
        query = "{}, {'loginData': {'userId': un}}"
        if db.find_one(query):
            return True
        return False

    def create(self, userName, password, pinCode, nickName, *args, **kwargs):
        wdb = dataBase.conf("write")
        db = wdb["userLogins"]
        un = userName
        pw = password
        pin = pinCode
        nn = nickName
        uu = User()
        uc = uu.get_userId(un)
        if uc is True:
            pw = password
            pin = pinCode
            pin0 = pwhash.argon2id.str(pin.encode("UTF-8"))
            pw0 = pwhash.scryptsalsa208sha256_str(pw.encode("utf8"))
            nn = nickName
            isAdmin = False
            msc = datetime.now(tz=timezone.utc)
            try:
                print("userId is available,... creating account")
                result = db.insert_one(
                    {
                        "loginData": {
                            "userId": un,
                            "password": pw0,
                            "pinCode": pin0,
                            "nickName": nn,
                            "isAdmin": isAdmin,
                            "masterId": "100001",
                            "memberSince": msc,
                            "lastLogin": msc
                        }
                    }
                )
                if result.acknowledged:
                    context = "User created!"
                    return context
            except PyMongoError as err:
                context = err
                return context
        else:
            context = "user not created"
            return uc

    def checkPass(self, userName, password) -> False:
        """check user pass - return true if match"""
        un = userName
        pw = password
        e = {}
        e = self.getCreds(un)
        e2 = e["loginData"]
        un1 = e2["userId"]
        pp = e2["password"]
        cp = pwhash.verify_scryptsalsa208sha256(pp, pw.encode("UTF-8"))
        if cp is True:
            return True
        return False

    def checkPin(self, userName, pinCode) -> False:
        """check user pin - return true if match"""
        un = userName
        pi = pinCode
        e = {}
        e = self.getCreds(un)
        e2 = e["loginData"]
        un1 = e2["userId"]
        pin = e2["pinCode"]
        cp = pwhash.argon2id.verify(pin, pi.encode("UTF-8"))
        if cp is True:
            return True
        return False

    def isAdmin(self, userName, isAdmin) -> False:
        """checks whether user is admin"""
        un = userName
        ia = isAdmin
        e = {}
        e = self.getCreds(un)
        e2 = e["loginData"]
        pp = e2["pinCode"]
        cp = pwhash.argon2id.verify(pp, pw.encode("UTF-8"))
        if cp is True:
            return True
        return False

    @property
    def is_authenticated(self, userName) -> bool:
        un = userName
        if self.find(un) is True:
            if self.checkPass(un) is True:
                if self.checkPin(un) is True:
                    return True
        return False

    @property
    def display_name(self) -> str:
        return self.nickName

    @property
    def identity(self) -> int:
        return self.masterId

    def get_userId(self, userName):
        un = userName
        query = {"loginData.userId": {"$eq": un}}
        rdb = dataBase.conf("read")
        db = rdb["userLogins"]
        e = db.find_one(query)
        if e is None:
            context = "User ID is not yet in use"
            uc = True
            return uc
        context = "User ID exists.  Please choose another"
        uc = False
        return uc

    def getCreds(self, userName):
        un = userName
        e = {}
        query = {"loginData.userId": {"$eq": un}}
        rdb = dataBase.conf("read")
        db = rdb["userLogins"]
        e = db.find_one(query)
        if e is None:
            context = "Cannot find user info"
            uc = false
            return uc, context
        context = ""
        uc = True
        return e

    def multi():
        db = pymongo.MongoClient().theRing
        return db

    # Do something with db.


class userList:
    def __init__(self):
        self.userName: str

    def usersAll():
        db = dataBase.conf("read")
        rdb = db["userLogins"]
        usersAll = rdb.find({}, {"_id": 0, "loginData.userId": 1})
        return usersAll

    def dict_username(self) -> dict:
        d = {}
        for user in self.user_list:
            d[user.userName] = user
        return d

    def dict_id(self) -> dict:
        d = {}
        for user in self.user_list:
            d[user.identity] = user
        return d

    def add(self, user: User) -> bool:
        if user.identity in self.dict_id():
            return False
        self.user_list.append(user)
        return True

    def get_by_username(self, userName: str) -> typing.Optional[User]:
        self.userName = userName
        rdb = dataBase.conf("read")
        db = rdb["userLogins"]
        query = {"loginData.userId": {"$eq": userName}}
        userName = db.find_one(query)
        return userName

    def get_by_id(self, identifier: int) -> typing.Optional[User]:
        return self.dict_id().get(identifier)

    def user_loader(self, request: Request, userName: str):
        un = userName
        return self.find(un)


#      db.counters.insert({
# 	"loginData.masterId":"loginData.masterId",
# 	"sequence_value": 10000001
# })
# WriteResult({ "nInserted" : 1 })

# function getNextSequenceValue(nextSeq){
#    var sequenceDocument = db.counters.findAndModify({
#       query:{loginData.masterId: nextSeq },
#       update: {$inc:{sequence_value:1}},
#       new:true
#    });
#    return sequenceDocument.sequence_value;
# }
