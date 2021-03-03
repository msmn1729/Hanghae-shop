from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
import hashlib
import jwt
import datetime

SECRET_KEY = 'Pl^EqCCvnI(d3xDBFofHyxHxLtuBWs';
TOKEN_NAME = 'login_token';

app = Flask(__name__)

client = MongoClient('localhost', 27017)
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

        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

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
def getGoodsSearch():
    received_keywords = request.args.get("keywords");
    print('searched keywords: ', received_keywords);
    return render_template('goods.html', keywords=received_keywords);


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
