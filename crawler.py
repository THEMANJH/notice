import firebase_admin
from firebase_admin import credentials, firestore, messaging
import requests
from bs4 import BeautifulSoup
import urllib.parse

# 1. 파이어베이스 초기화
cred = credentials.Certificate("firebase_credential.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def get_inha_political_latest_id(url):
    """인하대 정외과 게시판에서 최신 일반 공지사항 번호를 추출하는 함수"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 인하대 게시판 테이블의 모든 행(tr)을 가져옵니다.
        rows = soup.select("table.artclTable tbody tr")
        
        for row in rows:
            # '_notice' 클래스가 붙은 상단 고정 필독 공지는 건너뜁니다.
            if "artclNotice" in row.get("class", []):
                continue
                
            # 일반 공지의 번호가 있는 태그를 찾습니다.
            num_td = row.select_one("td.artclNum")
            if num_td:
                num_text = num_td.text.strip()
                # 숫자로만 이루어진 진짜 글 번호라면 반환
                if num_text.isdigit():
                    return int(num_text)
    except Exception as e:
        print(f"❌ 크롤링 중 에러 발생: {e}")
    return None

def send_fcm_push(target_url, notice_id):
    """해당 URL을 구독한 유저들에게 FCM 토픽 푸시 알림을 발송하는 함수"""
    # URL 주소 기반으로 생성했던 안전한 토픽 ID 복원
    # 프론트엔드와 1:1로 매칭되는 알림방 이름입니다.
    import base64
    safe_topic = base64.b64encode(target_url.encode('utf-8')).decode('utf-8').replace("=", "")
    
    message = messaging.Message(
        notification=messaging.Notification(
            title="🏫 새로운 공지사항이 올라왔어요!",
            body=f"등록하신 게시판에 새 글이 등록되었습니다. (글 번호: {notice_id})"
        ),
        topic=safe_topic # 이 주소를 신청한 방에만 쏘기
    )
    
    response = messaging.send(message)
    print(f"🚀 푸시 알림 발송 성공! Message ID: {response}")

def run_crawler():
    print("🔄 공지사항 모니터링 크롤러 가동...")
    
    urls_ref = db.collection("urls")
    docs = urls_ref.stream()
    
    for doc in docs:
        data = doc.to_dict()
        target_url = data.get("url")
        last_saved_id = data.get("last_id", 0)
        
        print(f"\n[체크 중] {target_url}")
        
        # 인하대 정외과 URL인 경우 맞춤형 함수 실행
        if "inha.ac.kr" in target_url:
            current_top_id = get_inha_political_latest_id(target_url)
            
            if current_top_id and current_top_id > last_saved_id:
                print(f"🔥 새 공지 감지! (이전: {last_saved_id} -> 현재: {current_top_id})")
                
                # 1. DB 업데이트
                doc.reference.update({"last_id": current_top_id})
                # 2. 진짜 푸시 알림 쏘기
                send_fcm_push(target_url, current_top_id)
            else:
                print("✅ 변동 없음.")

if __name__ == "__main__":
    run_crawler()