from app import db

# データベースのテーブルを作成
def create_db():
    db.create_all()
    print("Database tables created.")

if __name__ == '__main__':
    create_db()
