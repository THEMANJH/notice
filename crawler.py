import firebase_admin
from firebase_admin import credentials, firestore, messaging
import requests
from bs4 import BeautifulSoup
import base64

# 1. 파이어베이스 초기화
try:
    cred = credentials.Certificate("firebase_credential.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ [SYSTEM] 파이어베이스 라이브러리 및 DB 연결 성공")
except Exception as e:
    print(f"❌ [SYSTEM] 파이어베이스 초기화 실패 마스터 키를 확인하세요: {e}")

def get_inha_political_latest_id(url):
    """인하대 정외과 게시판에서 최신 일반 공지사항 번호를 추출하는 함수"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select("table.artclTable tbody tr")
        
        for row in rows:
            if "artclNotice" in row.get("class", []):
                continue
            num_td = row.select_one("td.artclNum")
            if num_td:
                num_text = num_td.text.strip()
                if num_text.isdigit():
                    return int(num_text)
    except Exception as e:
        print(f"❌ [CRAWL ERROR] 인하대 사이트 파싱 실패: {e}")
    return None

def send_fcm_push(target_url, notice_id):
    """해당 URL을 구독한 유저들에게 FCM 토픽 푸시 알림을 발송하고 로그를 남기는 함수"""
    try:
        # 프론트엔드와 동일한 방식으로 토픽 ID 생성
        safe_topic = base64.b64encode(target_url.encode('utf-8')).decode('utf-8').replace("=", "")
        print(f"📡 [FCM] 발송 시도 예정 토픽 방 이름: {safe_topic}")
        
        message = messaging.Message(
            notification=messaging.Notification(
                title="🏫 새로운 공지사항이 올라왔어요!",
                body=f"등록하신 게시판에 새 글이 등록되었습니다. (글 번호: {notice_id})"
            ),
            topic=safe_topic
        )
        
        # 실제 구글 서버로 전송 후 응답 받기
        response = messaging.send(message)
        print(f"🚀 [FCM SUCCESS] 구글 서버로 신호 전달 완료! 메시지 ID: {response}")
        
    except Exception as e:
        print(f"❌ [FCM ERROR] 구글 푸시 서버가 발송을 거부했습니다. 원인: {e}")

def run_crawler():
    print("\n==============================================")
    print("🔄 공지사항 모니터링 크롤러 가동 시작...")
    print("==============================================")
    
    urls_ref = db.collection("urls")
    docs = urls_ref.stream()
    
    has_docs = False
    for doc in docs:
        has_docs = True
        data = doc.to_dict()
        target_url = data.get("url")
        last_saved_id = data.get("last_id", 0)
        
        # 빈 주소나 이상한 주소 스킵
        if not target_url or target_url == "https://":
            continue
            
        print(f"\n🔍 [체크 중] 타겟: {target_url}")
        print(f"📊 [DB 상태] 기억하고 있는 마지막 번호: {last_saved_id}")
        
        if "inha.ac.kr" in target_url:
            current_top_id = get_inha_political_latest_id(target_url)
            print(f"🌐 [웹 상태] 현재 인하대 실제 최신 번호: {current_top_id}")
            
            if current_top_id:
                if current_top_id > last_saved_id:
                    print(f"🔥 [🔥변동 감지🔥] 새 글 발견! ({last_saved_id} -> {current_top_id})")
                    
                    # 1. DB 업데이트 진행 및 확인 로그
                    doc.reference.update({"last_id": current_top_id})
                    print("💾 [DB UPDATE] 파이어베이스 Firestore에 최신 번호 갱신 완료")
                    
                    # 2. 푸시 발송
                    send_fcm_push(target_url, current_top_id)
                else:
                    print("✅ [변동 없음] 웹사이트 번호가 DB와 같거나 작습니다.")
            else:
                print("❌ [경고] 웹사이트에서 최신 번호 숫자를 긁어오지 못했습니다.")
                
    if not has_docs:
        print("📁 [DB EMPTY] 현재 Firestore 'urls' 컬렉션에 등록된 주소가 아무것도 없습니다.")
    print("\n==============================================")
    print("🏁 크롤러 실행 종료.")
    print("==============================================")

# if __name__ == "__main__":
    # run_crawler()
if __name__ == "__main__":
    # 원래 있던 run_crawler() 앞에 #을 붙여서 잠시 주석 처리(잠재우기) 합니다.
    # run_crawler() 
    
    # 🔥 [강제 발송 치트키] 코드를 실행하자마자 인하대 알림방으로 9999번 글 알림을 쏩니다!
    print("🚨 [TEST] 내 폰으로 진짜 크롤러 알림 강제 발송 시작...")
    send_fcm_push("https://political.inha.ac.kr/political/7753/subview.do", 9999)