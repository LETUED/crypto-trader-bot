#!/usr/bin/env python3
"""
Telegram Chat ID 확인 스크립트
"""

import requests
import json

TELEGRAM_TOKEN = "***REMOVED_TELEGRAM_TOKEN***"

def get_chat_id():
    """최근 메시지에서 Chat ID 확인"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['result']:
                print("📨 최근 메시지 목록:")
                print("=" * 50)
                
                for update in data['result'][-5:]:  # 최근 5개 메시지
                    if 'message' in update:
                        message = update['message']
                        chat_id = message['chat']['id']
                        user_name = message['from'].get('first_name', 'Unknown')
                        text = message.get('text', 'No text')
                        date = message['date']
                        
                        print(f"Chat ID: {chat_id}")
                        print(f"사용자: {user_name}")
                        print(f"메시지: {text}")
                        print(f"시간: {date}")
                        print("-" * 30)
                
                # 가장 최근 메시지의 Chat ID 반환
                latest_chat_id = data['result'][-1]['message']['chat']['id']
                print(f"✅ 사용할 Chat ID: {latest_chat_id}")
                return latest_chat_id
            else:
                print("❌ 메시지가 없습니다.")
                print("봇과 대화를 시작한 후 다시 실행하세요.")
                return None
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Telegram Chat ID 확인 중...")
    get_chat_id()