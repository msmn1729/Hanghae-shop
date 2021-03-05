from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.hanghaeshop

received_keywords: str = "플스 프로"

splitted = received_keywords.split(' ')

searchTarget = []

for string in splitted:
    searchTarget.append({"title": {"$regex": ".*" + string + ".*"}})

print(searchTarget)

# 여러 개의 조건을 사용한 검색
searchedGoods = db.goods.find({"$or": searchTarget})

# 정규표현식을 사용한 검색
# searchedGoods = db.goods.find({"title": {"$regex": ".*스4.*"}});

# text index를 활용한 검색
# searchedGoods = db.goods.find({"$text": [{"$search": "앙기모띠"}, {"$search": "플스4"}]})
for goods in searchedGoods:
    print(goods)

print(searchedGoods)
