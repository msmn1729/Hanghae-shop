import hashlib

from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.hanghaeshop


@app.route('/', methods=['GET'])
def home():
    return render_template('main.html')


@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/user/register', methods=['GET'])
def userRegisterGet():
    return render_template('modify_member_infomation.html')


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
    return render_template('goods.html', keyword=received_keywords);


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
