import firebase_admin
from firebase_admin import credentials, firestore, messaging
import requests
from bs4 import BeautifulSoup
import urllib.parse
import datetime # 🚨 시간을 기록하기 위해 추가됨

# 1. 파이어베이스 초기화
try:
    cred = credentials.Certificate("firebase_credential.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ [SYSTEM] 파이어베이스 라이브러리 및 DB 연결 성공")
except Exception as e:
    print(f"❌ [SYSTEM] 파이어베이스 초기화 실패 마스터 키를 확인하세요: {e}")

def get_inha_political_latest_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rows = soup.select("tbody tr")
        for row in rows:
            tds = row.find_all("td")
            if len(tds) < 2:
                continue
                
            num_text = tds[0].text.strip()
            
            if num_text.isdigit():
                a_tag = row.find("a")
                if a_tag and a_tag.get("href"):
                    href_link = a_tag["href"]
                    full_link = urllib.parse.urljoin(url, href_link)
                    title_text = a_tag.text.strip()
                    
                    return int(num_text), full_link, title_text
                    
    except Exception as e:
        print(f"❌ [CRAWL ERROR] 인하대 사이트 파싱 실패: {e}")
    
    return None, None, None

def send_multicast_push(tokens, notice_id, target_link, notice_title):
    if not tokens:
        print("💡 [FCM] 해당 주소를 구독 중인 기기 토큰이 없습니다. 발송을 생략합니다.")
        return

    safe_target_link = urllib.parse.quote(target_link, safe='')
    app_url = f"https://notice-jet.vercel.app/?redirect={safe_target_link}"

    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title="🏫 새 공지: " + notice_title,
                body=f"글 번호: {notice_id} | 터치하여 공지사항으로 워프!"
            ),
            webpush=messaging.WebpushConfig(
                fcm_options=messaging.WebpushFCMOptions(
                    link=app_url 
                )
            ),
            data={
                "click_action": app_url
            },
            tokens=tokens
        )
        
        response = messaging.send_each_for_multicast(message)
        print(f"🚀 [FCM SUCCESS] {response.success_count}개의 기기에 알림 발송 성공! (실패: {response.failure_count})")
        
    except Exception as e:
        print(f"❌ [FCM ERROR] 구글 푸시 서버 전송 실패. 원인: {e}")

def run_crawler():
    print("\n==============================================")
    print("🔄 고도화 공지사항 모니터링 크롤러 가동 시작...")
    print("==============================================")
    
    urls_ref = db.collection("urls")
    docs = urls_ref.stream()
    
    has_docs = False
    for doc in docs:
        has_docs = True
        data = doc.to_dict()
        target_url = data.get("url")
        last_saved_id = data.get("last_id", 0)
        tokens = data.get("tokens", [])
        
        if not target_url or target_url == "https://":
            continue
            
        print(f"\n🔍 [체크 중] 타겟: {target_url}")
        print(f"📊 [DB 상태] 기억하고 있는 마지막 번호: {last_saved_id}")
        
        if "inha.ac.kr" in target_url:
            current_top_id, target_link, notice_title = get_inha_political_latest_data(target_url)
            print(f"🌐 [웹 상태] 현재 인하대 실제 최신 번호: {current_top_id}")
            
            if current_top_id:
                if last_saved_id == 0 or current_top_id > last_saved_id:
                    print(f"🔥 [🔥변동 감지🔥] 새 글 발견! ({last_saved_id} -> {current_top_id})")
                    print(f"📝 [글 제목] {notice_title}")
                    
                    # 🚨 [추가됨] DB에 누적할 히스토리 데이터 조립
                    new_history = {
                        "id": current_top_id,
                        "title": notice_title,
                        "link": target_link,
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                    }
                    
                    # 🚨 [수정됨] last_id 갱신과 동시에 history 배열에 내역 추가!
                    doc.reference.update({
                        "last_id": current_top_id,
                        "history": firestore.ArrayUnion([new_history])
                    })
                    print("💾 [DB UPDATE] 파이어베이스 Firestore에 최신 번호 및 히스토리 갱신 완료")
                    
                    send_multicast_push(tokens, current_top_id, target_link, notice_title)
                else:
                    print("✅ [변동 없음] 웹사이트 번호가 DB와 같거나 작습니다.")
            else:
                print("❌ [경고] 웹사이트에서 최신 번호 숫자를 긁어오지 못했습니다.")
                
    if not has_docs:
        print("📁 [DB EMPTY] 현재 Firestore 'urls' 컬렉션에 등록된 주소가 아무것도 없습니다.")
    print("\n==============================================")
    print("🏁 크롤러 실행 종료.")
    print("==============================================")

if __name__ == "__main__":
    run_crawler()