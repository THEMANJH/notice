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
    event.notification.close();

    // 파이썬이 보내준 완제품 주소(notice-jet.../?redirect=...)를 그대로 꺼냅니다.
    let targetUrl = '/';
    if (event.notification.click_action) {
        targetUrl = event.notification.click_action;
    } else if (event.notification.data && event.notification.data.click_action) {
        targetUrl = event.notification.data.click_action;
    } else if (event.notification.data && event.notification.data.FCM_MSG && event.notification.data.FCM_MSG.data && event.notification.data.FCM_MSG.data.click_action) {
        targetUrl = event.notification.data.FCM_MSG.data.click_action;
    }

    // 아이폰 앱(PWA) 안에서 안전하게 우리 웹앱 주소를 엽니다.
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
            for (let i = 0; i < clientList.length; i++) {
                let client = clientList[i];
                if ('focus' in client) {
                    client.navigate(targetUrl);
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});