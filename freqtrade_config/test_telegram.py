#!/usr/bin/env python3
"""
Telegram 봇 연결 테스트 스크립트
LETUED Crypto Trader Bot 테스트용
"""

import requests
import json
from datetime import datetime

# Telegram 봇 설정
TELEGRAM_TOKEN = "***REMOVED_TELEGRAM_TOKEN***"
TELEGRAM_CHAT_ID = "***REMOVED_CHAT_ID***"

def test_telegram_connection():
    """Telegram 봇 연결 테스트"""
    try:
        # 봇 정보 확인
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
        response = requests.get(url)
        
        if response.status_code == 200:
            bot_info = response.json()
            print("✅ Telegram 봇 연결 성공!")
            print(f"   봇 이름: {bot_info['result']['first_name']}")
            print(f"   사용자명: @{bot_info['result']['username']}")
            return True
        else:
            print("❌ Telegram 봇 연결 실패!")
            print(f"   오류 코드: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Telegram 봇 테스트 중 오류: {e}")
        return False

def send_test_message():
    """테스트 메시지 전송"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""
🚀 **LETUED Crypto Trader Bot 테스트**

📅 시간: {current_time}
🤖 봇 상태: 정상 작동
📊 시스템: 연결 테스트 완료

✅ Telegram 알림 시스템이 성공적으로 구성되었습니다!

다음 알림을 받게 됩니다:
• 거래 진입/청산 알림
• 수익/손실 업데이트  
• 시스템 상태 알림
• 오류 및 경고 메시지

🎯 이제 실제 거래를 시작할 준비가 완료되었습니다!
        """
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            print("✅ 테스트 메시지 전송 성공!")
            print("   Telegram에서 메시지를 확인하세요.")
            return True
        else:
            print("❌ 테스트 메시지 전송 실패!")
            print(f"   오류 코드: {response.status_code}")
            print(f"   응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 메시지 전송 중 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🔧 LETUED Crypto Trader - Telegram 봇 테스트 시작")
    print("=" * 50)
    
    # 1. 봇 연결 테스트
    if test_telegram_connection():
        print()
        # 2. 테스트 메시지 전송
        send_test_message()
    
    print("\n" + "=" * 50)
    print("🏁 테스트 완료")

if __name__ == "__main__":
    main()