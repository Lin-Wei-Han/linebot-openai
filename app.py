from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

FINETUNE_MODEL_ID = 'gpt-4o-mini'

with open('./data/reference.txt', 'r', encoding='utf-8') as f:
    system_data = f.read()

@app.route('/callback', methods=['POST'])
def callback():
    body = request.json

    for event in body['events']:
        if event['type'] == 'message':
            message_type = event['message']['type']
            reply_token = event['replyToken']
            
            if message_type == 'sticker':
                reply_message(reply_token, "[貼圖]")
            elif message_type == 'text':
                user_message = event['message']['text']
                assistant_message = get_openai_reply(user_message)
                reply_message(reply_token, assistant_message)

    return jsonify({'status': 'success'}), 200

def reply_message(reply_token, text):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }

    body = {
        'replyToken': reply_token,
        'messages': [{'type': 'text', 'text': text}]
    }

    requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=body)

def get_openai_reply(user_message):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }

    data = {
        "model": FINETUNE_MODEL_ID,
        "messages": [
            {"role": "system", "content": system_data},
            {"role": "user", "content": user_message}
        ]
    }

    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    response_json = response.json()
    return response_json['choices'][0]['message']['content']

if __name__ == '__main__':
    app.run(port=8000)
