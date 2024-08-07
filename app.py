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

# 儲存訊息紀錄
message_history = []

@app.route('/')
def home():
    return ''

@app.route('/callback', methods=['POST'])
def callback():
    body = request.json

    for event in body['events']:
        if event['type'] == 'message':
            message_type = event['message']['type']
            reply_token = event['replyToken']
            user_id = event['source']['userId']  # 獲取用戶ID
            print(event)
            
            if message_type == 'text':
                user_message = event['message']['text']
                assistant_message = get_openai_reply(user_message)
                reply_message(reply_token, assistant_message)
                reply_message(reply_token, f"用戶ID是: {user_id}")
            else:
                reply_message(reply_token, "貓貓，鹿鹿看不懂這個")

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
    # 更新訊息紀錄
    message_history.append({"role": "user", "content": user_message})
    
    # 保留最近五則訊息
    if len(message_history) > 10:
        message_history.pop(0)
    
    # 組織對話上下文
    messages = [{"role": "system", "content": system_data}] + message_history

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }

    data = {
        "model": FINETUNE_MODEL_ID,
        "messages": messages
    }

    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    response_json = response.json()
    
    # 添加助手的回覆到訊息紀錄
    assistant_message = response_json['choices'][0]['message']['content']
    message_history.append({"role": "assistant", "content": assistant_message})
    
    # 保留最近五則訊息
    if len(message_history) > 10:
        message_history.pop(0)
    
    return assistant_message

if __name__ == '__main__':
    app.run(port=8000)
