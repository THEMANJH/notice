// 제공해주신 12.14.0 버전에 맞춘 compat(호환) 라이브러리 로드
importScripts('https://www.gstatic.com/firebasejs/12.14.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/12.14.0/firebase-messaging-compat.js');

// 제공해주신 회원님의 실제 설정값 적용 완료
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

// 앱이 꺼져있을 때(백그라운드) 푸시 알림이 오면 화면에 팝업을 띄우는 로직
messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] 백그라운드 메시지 수신: ', payload);

    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        // 기본 알림 아이콘
        icon: 'https://cdn-icons-png.flaticon.com/512/3602/3602149.png' 
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});