import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import openai

# 環境変数を読み込む
load_dotenv()

app = Flask(__name__)

# 環境変数からAPIキーを設定
openai.api_key = os.getenv('GPT_API_KEY')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    message = request.json['message']

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": message}
            ]
        )
        return jsonify({'response': response['choices'][0]['message']['content'].strip()})
    except Exception as e:
        return jsonify({'response': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
