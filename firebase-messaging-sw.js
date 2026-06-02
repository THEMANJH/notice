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

// 알림 배너 클릭 시 우리 웹페이지를 먼저 열고, 학교 주소를 쿼리스트링으로 전달
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    const schoolUrl = event.notification.data?.click_action || event.notification.click_action || '';
    
    // 🚨 내 Vercel 앱 주소 뒤에 학교 링크를 매달아서 엽니다.
    let ourAppUrl = 'https://notice-jet.vercel.app/'; 
    if (schoolUrl) {
        ourAppUrl += '?redirect=' + encodeURIComponent(schoolUrl);
    }

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
            // 이미 켜져 있는 우리 앱 탭이 있다면 그리로 가고, 없다면 새로 엽니다.
            for (let i = 0; i < clientList.length; i++) {
                let client = clientList[i];
                if ('focus' in client) {
                    client.navigate(ourAppUrl);
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(ourAppUrl);
            }
        })
    );
});