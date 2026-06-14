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

// 🚨 중복을 제거한 단 하나의 완벽한 워프 코드!
self.addEventListener('notificationclick', function(event) {
    console.log('[Service Worker] 알림 클릭 감지!', event);
    
    // 1. 클릭한 알림 배너를 화면에서 닫아줍니다.
    event.notification.close();

    // 2. 파이썬 크롤러가 보낸 data 안의 click_action(이동할 주소)을 꺼냅니다.
    let targetUrl = '/';
    if (event.notification.data && event.notification.data.click_action) {
        targetUrl = event.notification.data.click_action;
    } else if (event.notification.data && event.notification.data.FCM_MSG && event.notification.data.FCM_MSG.data && event.notification.data.FCM_MSG.data.click_action) {
        targetUrl = event.notification.data.FCM_MSG.data.click_action;
    }

    // 3. 핸드폰 브라우저 새 창을 열어 공지사항 주소로 강제 이동시킵니다!
    event.waitUntil(
        clients.openWindow(targetUrl)
    );
});