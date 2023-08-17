from db.dB import dataBase

rdb = dataBase.Config("read")
db = rdb["userData"]
from user import User

uu = User()
userName = "rjallen"
password = "changeMe"
nickName = "therealnix"
pinCode = "02020202"


uu = get_user()
db = get_db()
u = "rjallen"

uu.get_userId(u)

user = db.find({}, {"loginData.userId": un})
