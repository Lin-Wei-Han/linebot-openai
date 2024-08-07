from flask import Flask, request, jsonify
import threading
import schedule
import requests
import time
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

@app.route('/callback', methods=['POST'])
def callback():
    body = request.json

    for event in body['events']:
        if event['type'] == 'message':
            message_type = event['message']['type']
            reply_token = event['replyToken']
            
            if message_type == 'text':
                user_message = event['message']['text']
                assistant_message = get_openai_reply(user_message)
                reply_message(reply_token, assistant_message)
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

# 取得用戶 id 清單
def get_followers():
    url = 'https://api.line.me/v2/bot/followers/ids'
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    
    follower_ids = []
    next_cursor = None
    
    while True:
        params = {'limit': 1000}
        if next_cursor:
            params['start'] = next_cursor
        
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        follower_ids.extend(data['userIds'])
        
        if 'next' in data:
            next_cursor = data['next']
        else:
            break
    
    return follower_ids

def send_push_message(user_id, message):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }

    body = {
        'to': user_id,
        'messages': [{'type': 'text', 'text': message}]
    }

    response = requests.post('https://api.line.me/v2/bot/message/push', headers=headers, json=body)
    return response.status_code == 200

def send_scheduled_messages():
    follower_ids = get_followers()
    messages = [
        "早安！這是今天的第一則訊息。",
        "這是第二則訊息。祝您有美好的一天！"
    ]
    
    for user_id in follower_ids:
        for message in messages:
            send_push_message(user_id, message)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    # 設定排程任務
    schedule.every().monday.to_friday.at("12:35").do(send_scheduled_messages)
    
    # 在獨立的線程中運行排程器
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

    app.run(port=8000)
