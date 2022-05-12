from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import certifi
ca = certifi.where()

app = Flask(__name__)

SECRET_KEY = 'SPARTA'

client = MongoClient('mongodb+srv://test:sparta@cluster0.wyemi.mongodb.net/Cluster0?retryWrites=true&w=majority',
                     tlsCAFile=ca)
db = client.dbsparta


@app.route('/')
def main():
    movies = list(db.movies.find({}, {'_id': False}))
    return render_template('main.html', movies=movies)


@app.route('/kind/<key>')
def genre(key):
    movies = list(db.movies.find({"genre": str(key)}, {'_id': False}))
    return render_template('main.html', movies=movies)


@app.route('/detail/<key>')
def detail(key):
    movie = db.movies.find_one({"number": int(key)}, {'_id': False})
    reviews = list(db.reviews.find({"title": movie["title"]}, {'_id': False}))
    return render_template('detail.html', movie=movie, reviews=reviews)


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/api/signup', methods=['POST'])
def user_signup():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    doc = {
        "username": username_receive,
        "password": password_hash,
    }

    db.users.insert_one(doc)
    return jsonify({'result': 'success', 'msg': '회원가입이 완료되었습니다.'})


@app.route('/api/user_check', methods=['POST'])
def user_check():
    username_receive = request.form['username_give']
    exist = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exist': exist})


@app.route('/api/login', methods=['POST'])
def user_login():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': password_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')
        return jsonify({'result': 'success', 'token': token})
    else:
        return jsonify({'result': 'fail', 'msg': '아이디와 비밀번호가 일치하지 않습니다.'})


@app.route('/api/movie', methods=['POST'])
def movie_upload():
    token_receive = request.cookies.get('mytoken')

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        url_receive = request.form['url_give']

        exist = bool(db.movies.find_one({"url": url_receive}))

        if exist is True:
            return jsonify({'result': 'fail', 'msg': '이미 등록된 영화입니다.'})
        elif "https://movie.naver.com/movie/bi/mi/basic.naver?code=" not in url_receive:
            return jsonify({'result': 'fail', 'msg': '잘못된 URL입니다.'})
        else:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
            data = requests.get(url_receive, headers=headers)
            soup = BeautifulSoup(data.text, 'html.parser')

            title = soup.select_one('meta[property="og:title"]')['content']
            image = soup.select_one('meta[property="og:image"]')['content']
            description = soup.select_one('meta[property="og:description"]')['content']
            genre = soup.select_one(
                '#content > div.article > div.mv_info_area > div.mv_info > dl > dd:nth-child(2) > p > span:nth-child(1) > a').text

            count = len(list(db.movies.find({}, {'_id': False}))) + 1

            doc = {
                "number": count,
                "url": url_receive,
                "title": title,
                "image": image,
                "description": description,
                "genre": genre
            }

            db.movies.insert_one(doc)
            return jsonify({'result': 'success', 'msg': '영화가 등록되었습니다.'})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return jsonify({'msg': '로그인이 필요합니다.'})


@app.route('/api/review', methods=['POST'])
def review_upload():
    token_receive = request.cookies.get('mytoken')

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        userinfo = db.users.find_one({"username": payload["id"]})
        review_receive = request.form['review_give']
        title_receive = request.form['title_give']

        doc = {
            "title": title_receive,
            "username": userinfo["username"],
            "review": review_receive
        }

        db.reviews.insert_one(doc)
        return jsonify({'result': 'success', 'msg': '리뷰가 등록되었습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return jsonify({'result': 'fail', 'msg': '로그인이 필요합니다.'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5100, debug=True)
