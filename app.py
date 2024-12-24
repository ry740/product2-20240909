import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import openai
import requests
from dotenv import load_dotenv
from datetime import datetime  # タイムスタンプ用に追加
from flask_migrate import Migrate
from flask import session, redirect, url_for

# 環境変数を読み込む
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatgpt_app.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

# OpenAI APIキーの設定
openai.api_key = os.getenv('GPT_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# データベースモデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    experience = db.Column(db.Integer, default=0)  # 経験値の初期値は0
    level = db.Column(db.Integer, default=1)  # レベルの初期値は1
    chat_histories = db.relationship('ChatHistory', backref='user', lazy=True)
    icon = db.Column(db.String(255), default="/static/icons/default.png")  # アイコンのURL

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # タイムスタンプを追加

class CalorieEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)  # カレンダーの日付
    calories = db.Column(db.Integer, nullable=False)  # 摂取カロリー

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50),nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Thread {self.title}>'

# データベースを初期化する関数
def initialize_database():
    with app.app_context():
        db.create_all()

#YouTube Data APIを使って関連動画を検索
def search_youtube(query):
    youtube_url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',  # 動画のスニペット情報（タイトル、説明、サムネイルなど）を取得
        'q': query,         # ユーザーが入力した検索クエリ
        'type': 'video',    # 動画のみを検索
        'key': YOUTUBE_API_KEY,  # YouTube Data APIのキー（環境変数から取得）
        'maxResults': 5     # 最大5件の動画を取得
    }
    response = requests.get(youtube_url, params=params)
    videos = response.json().get('items', [])  # 結果から動画アイテムを取得
    return videos  # 動画リストを返す

#経験値が100に達するたびにレベルを1上げる関数を作成
def add_experience(user, points):
    user.experience += points
    while user.experience >= 100:  # 100経験値ごとにレベルアップ
        user.experience -= 100
        user.level += 1
        
        # アイコンを更新
        if user.level in LEVEL_ICONS:
            user.icon = LEVEL_ICONS[user.level]["icon"]
            
    db.session.commit()
    
# グローバルスコープに移動
LEVEL_ICONS = {
    1: {"icon": "/static/icons/1.png"},
    2: {"icon": "/static/icons/2.png"},
    3: {"icon": "/static/icons/3.png"},
    4: {"icon": "/static/icons/4.png"},
    5: {"icon": "/static/icons/5.png"},
}

def add_experience(user, points):
    user.experience += points
    while user.experience >= 100:
        user.experience -= 100
        user.level += 1

        # アイコンを更新
        if user.level in LEVEL_ICONS:
            user.icon = LEVEL_ICONS[user.level]["icon"]
            
    db.session.commit()

@app.route('/', endpoint='index')
def home():
    return render_template('index.html')

@app.route('/update_timestamps')
def update_timestamps():
    with app.app_context():
        histories = ChatHistory.query.filter(ChatHistory.timestamp == None).all()  # タイムスタンプがNoneの履歴を取得
        for history in histories:
            history.timestamp = datetime.utcnow()  # 現在の日時を適用
            db.session.commit()
    return 'Timestamps updated!'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # ユーザーがログイン済みの場合は、レベル確認ページにリダイレクト
    if 'username' in session:
        return redirect(url_for('user_stats'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # ユーザー名が既に存在するか確認
        if User.query.filter_by(username=username).first():
            return 'Username already exists!'

        # 新規ユーザーを作成し、データベースに保存
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # 登録時に100経験値を付与
        add_experience(new_user, 100)

        # ログインセッションを開始し、user_stats にリダイレクト
        session['username'] = username
        return redirect(url_for('user_stats'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('user_stats'))  # ログイン後に user_stats にリダイレクト
        else:
            return 'Invalid credentials!'
    
    return render_template('login.html')

@app.route('/user_stats')
def user_stats():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    return render_template('user_stats.html', user=user)

@app.route('/calories', methods=['GET', 'POST'])
def manage_calories():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        date = request.form['date']
        calories = int(request.form['calories'])

        # 既存エントリの確認
        entry = CalorieEntry.query.filter_by(user_id=user.id, date=date).first()

        if entry:
            entry.calories = calories  # 更新
        else:
            # 新規エントリ作成
            new_entry = CalorieEntry(user_id=user.id, date=date, calories=calories)
            db.session.add(new_entry)

        db.session.commit()

    # 過去のカロリー情報を取得
    entries = CalorieEntry.query.filter_by(user_id=user.id).order_by(CalorieEntry.date.desc()).all()

    return render_template('calories.html', entries=entries)

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
            # ChatGPTでの応答
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}]
            )
            chat_response = response.choices[0].message['content'].strip()

            # 新しいチャット履歴に保存
            new_history = ChatHistory(user_id=user.id, message=message, response=chat_response)
            db.session.add(new_history)
            db.session.commit()
            
            # メッセージ送信時に10経験値を付与
            add_experience(user, 10)

            # YouTube検索APIを使って関連動画を取得
            youtube_url = 'https://www.googleapis.com/youtube/v3/search'
            params = {
                'part': 'snippet',
                'q': message,  # チャットメッセージ内容で検索
                'type': 'video',
                'key': YOUTUBE_API_KEY,
                'maxResults': 3  # 結果数を制限
            }
            youtube_response = requests.get(youtube_url, params=params)
            videos = youtube_response.json().get('items', [])

            # 必要な情報をJSONで返す
            video_data = [{'title': video['snippet']['title'],
                           'description': video['snippet']['description'],
                           'thumbnail': video['snippet']['thumbnails']['default']['url'],
                           'videoId': video['id']['videoId']}
                          for video in videos]

            return jsonify({'response': chat_response, 'videos': video_data})
        except Exception as e:
            return jsonify({'response': str(e)})
    
    return render_template('chat.html')

@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    histories = ChatHistory.query.filter_by(user_id=user.id).order_by(ChatHistory.timestamp.desc()).all()  # タイムスタンプでソート
    
    return render_template('history.html', histories=histories)

# コメントページのHTMLを返すエンドポイント
@app.route('/community', methods=['GET'])
def community():
    # ユーザーがログインしていない場合はログインページにリダイレクト
    if 'username' not in session:
        return redirect(url_for('login'))
    # コメントページのHTMLを返す
    threads = Thread.query.all()
    return render_template('comment.html', threads=threads)

# コメント取得および投稿エンドポイント (GETとPOSTを1つにまとめる)
@app.route('/comments', methods=['GET', 'POST'])
def comments():
    # ログインしていない場合はログインページにリダイレクト
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'GET':
        # コメント取得処理
        comments = Comment.query.order_by(Comment.created_at.desc()).all()
        return jsonify([
            {
                "username": comment.username,
                "content": comment.content,
                "created_at": comment.created_at.strftime("%y-%m-%d %H:%M:%S")
            }
            for comment in comments
        ])
    elif request.method == 'POST':
        # コメント投稿処理
        data = request.get_json()
        username = data.get('username')
        content = data.get('comment')
        if not username or not content:
            return jsonify({"error": "Invalid input"}), 400
        new_comment = Comment(username=username, content=content)
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({"message": "Comment added"}), 201
    
@app.route('/add-thread', methods=['POST'])
def add_thread():
    data = request.get_json()
    title = data.get('title')
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    new_thread = Thread(title=title)
    db.session.add(new_thread)
    db.session.commit()
    return jsonify({'message': 'Thread added'}), 201

@app.route('/threads', methods=['GET'])
def get_threads():
    threads = Thread.query.all()
    return jsonify([{"title": thread.title} for thread in threads])
        
@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    youtube_url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'key': YOUTUBE_API_KEY,
        'maxResults': 3  # 必要に応じて表示数を調整
    }
    
    # YouTube APIへのリクエストを実行
    response = requests.get(youtube_url, params=params)
    videos = response.json().get('items', [])

    # 動画データを整形してJSONで返す
    video_data = [
        {
            'title': video['snippet']['title'],
            'description': video['snippet']['description'],
            'thumbnail': video['snippet']['thumbnails']['default']['url'],
            'videoId': video['id']['videoId']
        } for video in videos
    ]

    return jsonify({'videos': video_data})  # JSON形式で動画データを返す

if __name__ == '__main__':
    initialize_database()  # データベース初期化
    app.run(host='0.0.0.0', debug=True)
