importScripts('https://www.gstatic.com/firebasejs/12.14.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/12.14.0/firebase-messaging-compat.js');

firebase.initializeApp({
    apiKey: "AIzaSyDKUA3JA9HifyIAlIQ10cQhAt1HTdL16fc",
    authDomain: "notice-42db9.firebaseapp.com",
    projectId: "notice-42db9",
    storageBucket: "notice-42db9.firebasestorage.app",
    messagingSenderId: "577597948609",
    appId: "1:577597948609:web:afe3da019b67698a194a40",
    measurementId: "G-7B64BXTQCK"
});

const messaging = firebase.messaging();

self.addEventListener('notificationclick', function(event) {
    console.log('[Service Worker] 알림 클릭 감지!');
    
    // 1. 클릭한 알림 배너를 화면에서 닫아줍니다.
    event.notification.close();

    // 2. 파이썬이 보낸 타겟 주소(학교 공지사항 링크)를 확실하게 찾아냅니다.
    let targetUrl = '/';
    
    // 경우의 수 1: 구글 공식 fcm_options.link 로 들어온 경우 (현재 파이썬이 보내는 방식)
    if (event.notification.click_action) {
        targetUrl = event.notification.click_action;
    } 
    // 경우의 수 2: 파이썬 data 필드 안쪽 깊숙이 들어온 경우
    else if (event.notification.data && event.notification.data.FCM_MSG && event.notification.data.FCM_MSG.data && event.notification.data.FCM_MSG.data.click_action) {
        targetUrl = event.notification.data.FCM_MSG.data.click_action;
    } 
    // 경우의 수 3: 얕은 data 필드로 들어온 경우
    else if (event.notification.data && event.notification.data.click_action) {
        targetUrl = event.notification.data.click_action;
    }

    // 3. 아이폰 PWA(앱) 화면 유지를 위해 index.html의 redirect 기능으로 연결합니다.
    let finalUrl = '/';
    if (targetUrl !== '/' && targetUrl.startsWith('http')) {
        // 우리 앱 주소 뒤에 ?redirect=학교주소 를 매달아서 엽니다.
        finalUrl = 'https://notice-jet.vercel.app/?redirect=' + encodeURIComponent(targetUrl);
    }

    // 4. 새 창(또는 기존 창)을 열어 목적지로 워프!
    event.waitUntil(
        clients.openWindow(finalUrl)
    );
});