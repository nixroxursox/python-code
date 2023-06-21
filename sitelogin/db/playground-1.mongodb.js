// MongoDB Playground
// Use Ctrl+Space inside a snippet or a string literal to trigger completions.
import nacl
from nacl import pwhash, utils, encoding 
import datetime


chkUser = "test"
password = "test"
pin = "000000"
a = True
// The current database to use.
use('locker');


// Create a new document in the collection.
db.getCollection('luser').insertOne({
    "username": chkUser,
    "password": pwhash.scryptsalsa208sha256_str(password),
    "pin": pwhash.scryptsalsa208sha256_str(pin),
    "isActive": True,
    "isVendor": False,
    "broquerage": int(3),
    "created": datetime.datetime.now(),
    "vendorBond": float(500.0),
    "is_admin": a,
    "identifier": utils.random(32).hex()

});
