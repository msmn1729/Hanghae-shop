from flask import Flask, render_template, jsonify, request

app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    return render_template('main.html')


@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/user/register', methods=['GET'])
def userRegister():
    return render_template('modify_member_infomation.html')


@app.route('/goods/search', methods=['GET'])
def getGoodsSearch():
    received_keywords = request.args.get("keywords");
    print('searched keywords: ', received_keywords);
    return render_template('goods.html', keyword=received_keywords);


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
