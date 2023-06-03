from pymongo.mongo_client import MongoClient as mc
from pymongo.errors import PyMongoError
from nacl import pwhash, utils, exceptions
import time
import datetime
from decouple import config
from test.test_userdict import UserDictTest

# Configuration from environment variables or '.env' file.

ru = config('readUser')
wu = config('writeUser')
rp = config('readPass')
wp = config('writePass')
dbrUri = config('dbrUri')
dbwUri = config('dbwUri')


class dataBase():

    def __init__(self, db, col):
        self.db = "locker"
        self.col = col
    
    def Config(method):
        authSource = "admin"
        mechanism = "SCRAM-SHA-256"
        dbObj = "locker"
        host = "10.137.0.32"
        port = 27017
        if method == "read":
            dbUser = ru
            dbPass = rp
        else:
            dbUser = wu
            dbPass = wp
        client = mc(host, port, username=dbUser, password=dbPass, authSource=authSource, authMechanism=mechanism)
        db = client[dbObj]
        return db
    # def readDb(col):
    #     try:
    #         client = dataBase.Config("read")
    #         rcol = client[col]
    #         return rcol
    #     except PyMongoError as e:
    #         print(e)

    # def writeDb(col):
    #     try:
    #         client = dataBase.Config("write")
    #         rcol = client[col]
    #         return rcol
    #     except PyMongoError as e:
    #         print(e)
            
    def find(dbDict):
        try:
            dbCol, fuserId, fpasswd, fpin_code, = dbDict
            dbr = self.Config("read")
            rcol = dbr["luser"]
            try:
                dbUserId, dbPasswd, dbPinCode = rcol.find_one({}, "_id": 0, "userId": 1, "passwd": 1, "pin_code": 1)
                if dbDict[fuserId] == userId:
                    if pwhash.str(password, chkUser[password]) == True:
                        if pwhash.str(pin_code, chkUser[pin_code]) == True:
                            return userId
                        else:
                            return False
                    else:
                        return False
                return True
            except PyMongoError as e:
                print(e)
        except PyMongoError as e:
            print(e)

    def findAllUsers():
        try:
            db = self.readDb("locker","luser")
            dbr = db["locker"]
            rcol = dbr["luser"]
            userinfo = rcol.findMany({}, {'_id': 0, 'username': 1})
            return userinfo
        except PyMongoError as e:
            print(e)

    def addUser(chkUser, password, pin, a):
        a = a
        try:
            db = dataBase.getdb()
            coll = db["userBase"]
            data = ({'username': chkUser,
                'password': pwhash.scryptsalsa208sha256_str(password),
                'pin': pwhash.scryptsalsa208sha256_str(pin),
                'isActive': True,
                'isVendor': False,
                'broquerage': int(3),
                'created': datetime.datetime.now(),
                'vendorBond': float(500.0),
                'is_admin': a,
                'identifier': utils.random(32).hex()
                })
            result = coll.insert_one(data)
            if result:
                return True
            else:
                return False
        except Exception as e:
            print("An exception occurred :", e)
            return False

    def modUser(chkUser, appPass, newAppPass, pin, newPin):
        try:
            db = dataBase.getdb()
            coll = db["userBase"]
            data = ({'username': chkUser})
            if data:
                update = coll.find_one_and_update({'username': chkUser}, { '$set': { 'appPass': newAppPass, 'pin': newPin}})
                return update.AFTER
        except Exception as e:
            print("An exception occurred :", e)
            return False


# authSource=the_database&authMechanism=SCRAM-SHA-256"