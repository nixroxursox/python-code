import time
import datetime
from urllib.parse import quote_plus
from pymongo.mongo_client import MongoClient as mc
from pymongo.errors import PyMongoError
from nacl import pwhash, utils, exceptions
from decouple import config
from test.test_userdict import UserDictTest
import nacl
from nacl import pwhash


# directory reach


# Configuration from environment variables or '.env' file.

ru = config("readUser")
wu = config("writeUser")
rp = config("readPass")
wp = config("writePass")
dbrUri = config("dbrUri")
dbwUri = config("dbwUri")


class dataBase:
    def __init__(self):
        self.db = "theRing"
        self.col = "userData"
        self.method = None

    def Config(method):
        authSource = "theRing"
        mechanism = "SCRAM-SHA-256"
        dbObj = "theRing"
        # host = "%2Ftmp%2Fmongodb-27017.sock"
        host = "localhost"
        port = 27017
        if method == "read":
            dbUser = ru
            dbPass = rp
        else:
            dbUser = wu
            dbPass = wp
        client = mc(
            host,
            port,
            username=dbUser,
            password=dbPass,
            authSource=authSource,
            authMechanism=mechanism,
        )
        db = client[dbObj]
        return db

    def connect(self, how):
        type = how
        rdb = self.Config(how)
        db = rdb["userData"]
        return db

    def connX509(self):
        client = MongoClient(
            "example.com",
            authMechanism="MONGODB-X509",
            tls=True,
            tlsCertificateKeyFile="/path/to/client.pem",
            tlsCAFile="/path/to/ca.pem",
        )
        db = client["theRing"]
        return db

    def disconnect(self):
        return db.close()

    # def checkPass(dbDict):
    #     if dataBase.findUser == True:
    #         try:
    #             dbr = dataBase.Config("read")
    #             rcol = dbr["userData"]
    #             pw = dbDict["password"]
    #             dbp = dbDict["pinCode"]
    #             password = rcol.find({},{'_id': 0, 'userId': 1, 'password': 1, 'pin_code': 1})
    #             check = pwhash.verify(password[2], pw)
    #             checkPin = pwhash.verify(password[3], dbp)
    #             if check == True and checkPin == True:
    #                 return True
    #             else:
    #                 return False
    #         except Exception as e:
    #             return e
    #     else:
    #         return False
    #         if dbDict[fuserId] == fuserId:
    #             if pwhash.str(fpasswd, chkUser[password]) == True:
    #                 if pwhash.str(pin_code, chkUser[pin_code]) == True:
    #                     return userId
    #                 else:
    #                     return False
    #             else:
    #                 return Fals
    #         return True

    def allUsers():
        try:
            dbr = dataBase.Config("read")
            rcol = dbr["userData"]
            userinfo = rcol.findMany({}, q.findMany())
            return userinfo
        except PyMongoError as e:
            print(e)

    # def addUser(chkUser, password, pin, a):
    #     try:
    #         (
    #             fuserId,
    #             fpasswd,
    #             fpinCode,
    #         ) = dbDict
    #         dbr = dataBase.Config("read")
    #         rcol = dbr["userData"]
    #         data = {
    #             "username": chkUser,
    #             "password": pwhash.scryptsalsa208sha256_str(password),
    #             "pin": pwhash.scryptsalsa208sha256_str(pin),
    #             "isActive": True,
    #             "isVendor": False,
    #             "broquerage": int(3),
    #             "created": datetime.datetime.now(),
    #             "vendorBond": float(500.0),
    #             "is_admin": a,
    #             "identifier": utils.random(32).hex(),
    #         }
    #         result = coll.insert_one(data)
    #         if result:
    #             return True
    #         else:
    #             return False
    #     except Exception as err:
    #         print("An exception occurred :", err)
    #         return False

    # def modUser(chkUser, appPass, newAppPass, pin, newPin):
    #     try:
    #         dbr = dataBase.Config("write")
    #         rcol = dbr["userData"]
    #         data = rcol.find_one_and_update({"username": chkUser})
    #         if data:
    #             update = rcol.findOne({}, notused.getUserCreds())
    #             return update.AFTER
    #     except Exception as e:
    #         print("An exception occurred :", e)
    #         return False


# authSource=the_database&authMechanism=SCRAM-SHA-256"


class q:
    def __init__(self, user):
        self.query = None
        self.user = None

    def findUser(self):
        return {"_id": 0, "userId": 1}

    def getUserCreds():
        return {"_id": 0, "userId": 1, "password": 1, "pinCode": 1}

    def find_one_and_update():
        return "({'username': chkUser}, { '$set': { 'appPass': newAppPass, 'pin': newPin}})"

    def insert_one():
        record = '{"userId": fuserId, "password": fpasswd, "pin_code": fpinCode, "NickName": fnickName}'
        return record
