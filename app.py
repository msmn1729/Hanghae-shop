from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from bson.json_util import dumps
import datetime
import hashlib
import jwt

SECRET_KEY = 'Pl^EqCCvnI(d3xDBFofHyxHxLtuBWs';
TOKEN_NAME = 'login_token';

app = Flask(__name__)

client = MongoClient('localhost', 27017)  # 로컬
# client = MongoClient('mongodb://test:test@localhost', 27017) # 서버 배포할 때 아이디:비밀번호 형식 현재는 둘 다 test
db = client.hanghaeshop


def tryGetUserInfoWithToken(received_token: str):
    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(received_token, SECRET_KEY, algorithms=['HS256'])
        # print('token: ', received_token)
        # print('payload: ', payload)

        id = payload['id']

        userInfo = db.user.find_one({'id': id}, {'_id': 0})
        return {'success': True, 'message': '사용자 정보를 성공적으로 불러왔습니다.', 'userInfo': userInfo}

    # 토큰 유효기간 만료
    except jwt.ExpiredSignatureError:
        return {'success': False, 'message': '로그인 시간이 만료되었습니다.'}
    # 토큰 디코딩 에러
    except jwt.exceptions.DecodeError:
        return {'success': False, 'message': '로그인 정보가 존재하지 않습니다.'}


@app.route('/', methods=['GET'])
def home():
    received_token = request.cookies.get(TOKEN_NAME);

    return render_template('main.html')


@app.route('/user/login', methods=['GET'])
def userLoginPage():
    return render_template('login.html')


@app.route('/user/login', methods=['POST'])
def userLogin():
    received_id = request.form['id_give']
    received_password = request.form['password_give']

    hashed_password = hashlib.sha256(received_password.encode('utf-8')).hexdigest()

    finded_user = db.user.find_one({'id': received_id, 'password': hashed_password})

    # 찾으면 JWT 토큰을 만들어 발급합니다.
    if finded_user is not None:
        # JWT 토큰에는, payload와 시크릿키가 필요합니다.
        # 시크릿키가 있어야 토큰을 디코딩(=풀기) 해서 payload 값을 볼 수 있습니다.
        # 아래에선 id와 exp를 담았습니다. 즉, JWT 토큰을 풀면 유저ID 값을 알 수 있습니다.
        # exp에는 만료시간을 넣어줍니다. 만료시간이 지나면, 시크릿키로 토큰을 풀 때 만료되었다고 에러가 납니다.
        payload = {
            'id': received_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }

        # token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        token = str(token)  # 토큰 형변환(로컬에선 불필요하지만 서버에서는 없으면 오류)

        # token을 줍니다.
        return jsonify({'success': True, 'message': '로그인에 성공하였습니다.', TOKEN_NAME: token})

    return jsonify({'success': False, 'message': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/user/register', methods=['GET'])
def userRegisterPage():
    return render_template('sign_up.html')


@app.route('/user/register', methods=['POST'])
def userRegisterPost():
    received_id = request.form['id_give']
    received_password = request.form['password_give']
    received_email = request.form['email_give']

    user_info = db.user.find_one({"id": received_id})
    if user_info is not None:
        return jsonify({'success': False, 'message': '이미 이 아이디를 사용중인 회원이 있습니다.'})

    user_info = db.user.find_one({"id": received_email})
    if user_info is not None:
        return jsonify({'success': False, 'message': '이미 이 이메일을 사용중인 회원이 있습니다.'})

    hashed_password = hashlib.sha256(received_password.encode('utf-8')).hexdigest()
    db.user.insert_one({'id': received_id, 'password': hashed_password, 'email': received_email})
    return jsonify({'success': True, 'message': '회원가입에 성공하였습니다.'})


@app.route('/goods/search', methods=['GET'])
def goodsSearchPage():
    received_keywords: str = request.args.get("keywords")

    # 검색어를 ' '(빈 칸)으로 쪼갠 뒤, 쪼개진 단어들이 제목에 포함되어 있는지 검사합니다.
    # 한 단어라도 포함되어 있다면 검색 결과에 나타나게 됩니다.
    splitted_keywords = received_keywords.split(' ')

    search_condition_list = []
    for string in splitted_keywords:
        search_condition_list.append({"title": {"$regex": ".*" + string + ".*"}})

    ## _id로 상품페이지를 구분하도록함
    # searched_goods = list(db.goods.find({"$or": search_condition_list}, {'_id': False}))
    searched_goods = list(db.goods.find({"$or": search_condition_list}))

    # DEBUG 검색 결과를 확인하는 테스트코드입니다.
    for goods in searched_goods:
        print(goods)

    return render_template('goods.html', keywords=received_keywords,
                           searched_goods=dumps(searched_goods, ensure_ascii=False))


####################################################
####################################################
####################################################


## 상품 등록 API
@app.route('/goods/create', methods=['GET'])
def goods_create_page():
    return render_template('goods_upload.html')


@app.route('/goods/create', methods=['POST'])
def goods_create():
    title_receive = request.form['title_give']
    price_receive = request.form['price_give']
    desc_receive = request.form['desc_give']
    now = datetime.datetime.now()
    print('%02d/%02d/%04d %02d:%02d:%02d' % (now.month, now.day, now.year, now.hour, now.minute, now.second))
    cur_time = str(now.year) + '/' + str(now.month).zfill(2) + '/' + str(now.day).zfill(2) + ' ' + str(now.hour).zfill(2) + ':' + str(now.minute).zfill(2) + ':' + str(now.second).zfill(2)

    doc = {
        'title': title_receive,
        'price': price_receive,
        'desc': desc_receive,
        'upload_time': cur_time
    }
    db.goods.insert_one(doc);

    return jsonify({'result': 'success', 'msg': '글 등록 완료!\n\n메인 페이지로 이동합니다.'})


@app.route('/goods/read/<keyword>')
def goods_info_page(keyword):
    goods_list = list(db.goods.find({}))
    upload_time = 'asd'
    for goods in goods_list:
        if str(goods['_id']) == keyword:
            title = goods['title']
            price = goods['price']
            desc = goods['desc']
            print(goods['upload_time'])
            if goods['upload_time'] != None:
                upload_time = goods['upload_time']

    # print(upload_time)
    return render_template('goods_info.html', title=title, price=price,
                           desc=desc, upload_time=upload_time)


####################################################
####################################################
####################################################

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
