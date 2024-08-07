import requests
import time
import os

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

def send_push_message(user_id, message):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }

    body = {
        'to': user_id,
        'messages': [{'type': 'text', 'text': message}]
    }

    try:
        response = requests.post('https://api.line.me/v2/bot/message/push', headers=headers, json=body)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(e)
        return False

def send_scheduled_messages():
    follower_ids = ['Ud66dd5cfdad8a5fdbb2828dcd79a757f', 'U3c38a17508a27f1d47ff9c88154c63f3']
    messages = [
        "起床了！！！！！記得刷牙洗臉捏",
        "手機、鑰匙、錢包"
    ]
    
    success_count = 0
    for user_id in follower_ids:
        for message in messages:
            if send_push_message(user_id, message):
                success_count += 1
            
            time.sleep(1)

if __name__ == '__main__':
    send_scheduled_messages()