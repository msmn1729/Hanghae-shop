from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.hanghaeshop

searchedGoods = db.goods.find().sort([('upload_time', -1)]).limit(20)
for goods in searchedGoods:
    print(goods)