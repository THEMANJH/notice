import firebase_admin
from firebase_admin import credentials, firestore, messaging
import requests
from bs4 import BeautifulSoup
import urllib.parse

# 1. 파이어베이스 초기화
try:
    cred = credentials.Certificate("firebase_credential.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ [SYSTEM] 파이어베이스 라이브러리 및 DB 연결 성공")
except Exception as e:
    print(f"❌ [SYSTEM] 파이어베이스 초기화 실패 마스터 키를 확인하세요: {e}")

def get_inha_political_latest_data(url):
    """클래스명(이름표)에 의존하지 않고, 테이블 뼈대 구조만으로 
       순수 일반 공지사항 번호와 링크를 추출하는 강력한 파싱 함수"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'  # 한글 깨짐 및 파싱 오류 방지
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 게시판의 몸통(tbody) 안에 있는 모든 행(tr)을 긁어옵니다.
        rows = soup.select("tbody tr")
        
        for row in rows:
            # 해당 행에 있는 모든 칸(td)을 리스트로 뽑습니다.
            tds = row.find_all("td")
            
            # 칸이 2개 이상 없는 이상한 줄은 무시합니다.
            if len(tds) < 2:
                continue
                
            # 2. 보통 첫 번째 칸(tds[0])이 번호 칸입니다. 양옆 공백을 자르고 가져옵니다.
            num_text = tds[0].text.strip()
            
            # 3. 만약 첫 번째 칸의 텍스트가 '공지'가 아니라 '순수 숫자'로만 이루어져 있다면? (일반 공지 확정)
            if num_text.isdigit():
                # 해당 줄 어딘가에 있는 링크(a 태그)를 잡아냅니다.
                a_tag = row.find("a")
                
                if a_tag and a_tag.get("href"):
                    href_link = a_tag["href"]
                    # 상대 주소를 클릭 가능한 완벽한 전체 인터넷 주소로 조립
                    full_link = urllib.parse.urljoin(url, href_link)
                    return int(num_text), full_link
                    
    except Exception as e:
        print(f"❌ [CRAWL ERROR] 인하대 사이트 파싱 실패: {e}")
    
    return None, None

def send_multicast_push(tokens, notice_id, target_link):
    """DB에서 꺼내온 기기 토큰 리스트를 기반으로 멀티캐스트(다중) 핀포인트 푸시를 발송하는 함수"""
    if not tokens:
        print("💡 [FCM] 해당 주소를 구독 중인 기기 토큰이 없습니다. 발송을 생략합니다.")
        return

    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title="🏫 새로운 공지사항이 올라왔어요!",
                body=f"등록하신 게시판에 새 글이 등록되었습니다. (글 번호: {notice_id})\n터치하면 공지사항으로 이동합니다."
            ),
            # 🚨 구글 공식 표준 웹푸시 링크 양식으로 에러 해결!
            webpush=messaging.WebpushConfig(
                fcm_options=messaging.WebpushFCMOptions(
                    link=target_link
                )
            ),
            # 서비스 워커가 확실하게 낚아챌 수 있도록 data에도 안전 장치 추가
            data={
                "click_action": target_link
            },
            tokens=tokens
        )
        
        # 🚨 [여기 수정됨!!] 최신 파이썬 라이브러리 규격에 맞춰 함수 이름 변경
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
            current_top_id, target_link = get_inha_political_latest_data(target_url)
            print(f"🌐 [웹 상태] 현재 인하대 실제 최신 번호: {current_top_id}")
            
            if current_top_id:
                # DB가 초기 상태(0)이거나 진짜 새 글이 업데이트되었을 때 실행
                if last_saved_id == 0 or current_top_id > last_saved_id:
                    print(f"🔥 [🔥변동 감지🔥] 새 글 발견! ({last_saved_id} -> {current_top_id})")
                    print(f"🔗 [이동 링크] {target_link}")
                    
                    # 1. DB 업데이트 진행
                    doc.reference.update({"last_id": current_top_id})
                    print("💾 [DB UPDATE] 파이어베이스 Firestore에 최신 번호 갱신 완료")
                    
                    # 2. 멀티캐스트 푸시 발송
                    send_multicast_push(tokens, current_top_id, target_link)
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