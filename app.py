from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for
from pymongo import MongoClient
from bson.json_util import dumps
from bson.objectid import ObjectId
import datetime
import hashlib
import jwt
from werkzeug.utils import secure_filename
import hashlib
import jwt
import datetime
import os
import ast

SECRET_KEY = 'Pl^EqCCvnI(d3xDBFofHyxHxLtuBWs';
TOKEN_NAME = 'login_token';

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# client = MongoClient('localhost', 27017)  # 로컬
client = MongoClient('mongodb://test:test@localhost', 27017)  # 서버 배포할 때 아이디:비밀번호 형식 현재는 둘 다 test
db = client.hanghaeshop


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def tryGetUserInfoWithToken(received_token: str):
    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(received_token, SECRET_KEY, algorithms=['HS256'])
        # print('token: ', received_token)
        # print('payload: ', payload)

        id = payload['id']

        user_info = db.user.find_one({'id': id}, {'_id': 0})
        return {'success': True, 'message': '사용자 정보를 성공적으로 불러왔습니다.', 'user_info': user_info}

    # 토큰 유효기간 만료
    except jwt.ExpiredSignatureError:
        return {'success': False, 'message': '로그인 시간이 만료되었습니다.'}
    # 토큰 디코딩 에러
    except jwt.exceptions.DecodeError:
        return {'success': False, 'message': '로그인 정보가 존재하지 않습니다.'}


@app.route('/', methods=['GET'])
def home():
    received_token = request.cookies.get(TOKEN_NAME)
    check_token_validate_result = tryGetUserInfoWithToken(received_token)

    isLogin = 0
    if check_token_validate_result['success']:
        isLogin = 1

    latest_goods = db.goods.find().sort([('upload_time', -1)]).limit(12)

    return render_template('main.html', isLogin=isLogin, latest_goods=dumps(latest_goods, ensure_ascii=False))


@app.route('/greeting', methods=['GET'])
def greeting():
    return render_template('greeting.html')


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
        token = str(token, encoding="utf-8")  # 토큰 형변환(로컬에선 오히려 에러가 뜨지만 서버에서는 없으면 오류)
        print('payload: ', payload)
        print('token: ', token)

        print('str(token)', token)

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
    # 글 작성 페이지에 들어가기 전에 클라이언트의 토큰이 유효한지 확인합니다.
    received_token = request.cookies.get(TOKEN_NAME);
    check_token_validate_result = tryGetUserInfoWithToken(received_token)

    if check_token_validate_result['success'] is False:
        return redirect(url_for('userLoginPage'))

    return render_template('goods_upload.html')


@app.route('/goods/create', methods=['POST'])
def goods_create():
    # 글 업로드 직전에 클라이언트의 토큰이 유효한지 확인합니다.
    received_token = request.cookies.get(TOKEN_NAME);
    check_token_validate_result = tryGetUserInfoWithToken(received_token)

    print(check_token_validate_result)

    if check_token_validate_result['success'] is False:
        return jsonify({'result': 'fail', 'msg': '올바른 토큰이 아닙니다. 다시 로그인하여 토큰을 재발급 받아주세요.'})

    # 클라이언트로부터 전달받은 값들로 판매글을 db에 등록합니다.
    user_id = check_token_validate_result['user_info']['id']

    title_receive = request.form['title_give']
    price_receive = request.form['price_give']
    desc_receive = request.form['desc_give']
    images_receive = request.form['images_give']
    upload_time = datetime.datetime.now()

    images = ast.literal_eval(images_receive)

    doc = {
        'seller_id': user_id,
        'title': title_receive,
        'price': price_receive,
        'desc': desc_receive,
        'upload_time': upload_time,
        'images': images

    }
    db.goods.insert_one(doc);

    return jsonify({'result': 'success', 'msg': '글 등록 완료!\n\n메인 페이지로 이동합니다.'})


@app.route('/goods/read/<goods_id>')
def goods_info_page(goods_id):
    goods = db.goods.find_one({'_id': ObjectId(goods_id)})

    if goods is None:
        return jsonify({'result': 'fail', 'msg': '해당하는 ID의 물품이 없습니다.'})

    upload_time = 'undefinded'
    title = goods['title']
    price = goods['price']
    desc = goods['desc']
    images = goods['images']
    seller_id = goods['seller_id']

    if 'upload_time' in goods:
        upload_time = goods['upload_time']

    # print(upload_time)
    return render_template('goods_info.html', title=title, price=price,
                           desc=desc, upload_time=upload_time, images=images, seller_id=seller_id)


@app.route('/goods/image', methods=['POST'])
def upload_goods_image():
    # 이미지 업로드 전에 클라이언트의 토큰이 유효한지 확인합니다.
    received_token = request.cookies.get(TOKEN_NAME);
    check_token_validate_result = tryGetUserInfoWithToken(received_token)

    if check_token_validate_result['success'] is False:
        return jsonify({'success': False, 'message': '올바른 토큰이 아닙니다. 다시 로그인하여 토큰을 재발급 받아주세요.'})

    # 클라이언트로부터 건네져 온 파일이 정상적인 이미지 파일인지 확인합니다.
    received_file = request.files['file_give']
    print(received_file)

    if received_file is None:
        return jsonify({"success": False, "message": "올바른 사진을 업로드해주세요."})

    if received_file.filename == '':
        return jsonify({"success": False, "message": "올바른 사진을 업로드해주세요."})

    if allowed_file(received_file.filename) is False:
        return jsonify({"success": False, "message": "허용되는 포맷의 이미지가 아닙니다."})

    filename_splitted = received_file.filename.rsplit('.', 1)

    if len(filename_splitted) != 2:
        return jsonify({"success": False, "message": "올바른 확장자의 파일을 업로드해주세요."})

    # 이미지 파일명을 이미지 파일의 ID로 설정합니다.
    # 이미지 ID는 이미지 파일명의 해싱값 + 이미지 파일의 본래 확장자로 구성됩니다.
    # ex: molang.jpg -> de182d2f2eaade8a79ed66f4f0756aee80c7b1e82783fd149bee8ce8bb34ab88.jpg
    file_name = hashlib.sha256(filename_splitted[0].encode('utf-8')).hexdigest()
    file_extension = filename_splitted[1]
    image_id = file_name + '.' + file_extension

    file_savepath = os.path.join(app.config['UPLOAD_FOLDER'], image_id)

    # 사용자는 '\goods\image\\'에 image_id를 붙인 주소로 해당 이미지에 접근할 수 있습니다.
    image_path = '\\goods\\image\\' + image_id

    print(file_savepath, image_path)

    received_file.save(file_savepath)

    return jsonify({"success": True, "message": "사진을 정상적으로 업로드하였습니다.", "image": image_path})


@app.route('/goods/image/<image_id>', methods=['GET'])
def get_goods_image(image_id):
    image_local_path = os.path.join(app.config['UPLOAD_FOLDER'], image_id)
    if not os.path.exists(image_local_path):
        return jsonify({"success": False, "message": "올바른 이미지 ID가 아닙니다."})

    return send_file(image_local_path, mimetype="image")


## 상품 상세페이지 API
@app.route('/goods/read', methods=['GET'])
def goods_read_page():
    return render_template('goods_info.html')


####################################################
####################################################
####################################################


# ████████╗███████╗███████╗████████╗     ██████╗ ██████╗ ██████╗ ███████╗
# ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
#    ██║   █████╗  ███████╗   ██║       ██║     ██║   ██║██║  ██║█████╗
#    ██║   ██╔══╝  ╚════██║   ██║       ██║     ██║   ██║██║  ██║██╔══╝
#    ██║   ███████╗███████║   ██║       ╚██████╗╚██████╔╝██████╔╝███████╗
#    ╚═╝   ╚══════╝╚══════╝   ╚═╝        ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝

@app.route('/test/goods', methods=['GET'])
def test_goods():
    return render_template('test/upload-image_test.html')


####################################################
####################################################
####################################################

def initialize():
    if not os.path.isdir('uploads'):
        os.makedirs('uploads')


if __name__ == '__main__':
    initialize()

    app.run('0.0.0.0', port=5000, debug=True)
