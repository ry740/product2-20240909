from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os

# 環境変数を読み込む
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatgpt_app.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

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

def update_password_hashes():
    with app.app_context():
        users = User.query.all()

        for user in users:
            # 古いパスワードを取り出し、新しいハッシュに変換
            old_password = user.password
            try:
                # 新しいハッシュを生成
                new_password_hash = bcrypt.generate_password_hash('password').decode('utf-8')
                user.password = new_password_hash
                db.session.commit()
                print(f"Updated password hash for user: {user.username}")
            except Exception as e:
                print(f"Failed to update password hash for user: {user.username}. Error: {e}")

if __name__ == '__main__':
    initialize_database()
    update_password_hashes()
