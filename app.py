import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import openai
import requests
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatgpt_app.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# OpenAI APIキーの設定
openai.api_key = os.getenv('GPT_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# データベースモデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    chat_histories = db.relationship('ChatHistory', backref='user', lazy=True)

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)

# データベースを初期化する関数
def initialize_database():
    with app.app_context():
        db.create_all()

@app.route('/')
def home():
    # ユーザーがログインしているかどうかに関係なくindex.htmlを表示する
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        if User.query.filter_by(username=username).first():
            return 'Username already exists!'
        
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # デバッグ出力を追加
        print(f'Attempting login for user: {username}')
        
        user = User.query.filter_by(username=username).first()
        
        # ユーザーが見つかったか確認
        if user:
            print(f'User found: {username}')
            if bcrypt.check_password_hash(user.password, password):
                session['username'] = username
                return redirect(url_for('chat'))
            else:
                print('Password does not match.')
        else:
            print('User not found.')
        
        return 'Invalid credentials!'
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        message = request.json['message']
        user = User.query.filter_by(username=session['username']).first()

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}]
            )
            chat_response = response.choices[0].message['content'].strip()

            new_history = ChatHistory(user_id=user.id, message=message, response=chat_response)
            db.session.add(new_history)
            db.session.commit()

            return jsonify({'response': chat_response})
        except Exception as e:
            return jsonify({'response': str(e)})
    
    return render_template('chat.html')

@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    histories = ChatHistory.query.filter_by(user_id=user.id).all()
    
    return render_template('history.html', histories=histories)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        youtube_url = 'https://www.googleapis.com/youtube/v3/search'
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'key': YOUTUBE_API_KEY
        }
        response = requests.get(youtube_url, params=params)
        videos = response.json().get('items', [])

        return render_template('search_results.html', videos=videos)
    
    return render_template('search.html')

if __name__ == '__main__':
    initialize_database()  # データベース初期化
    app.run(host='0.0.0.0', debug=True)
