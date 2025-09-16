function isMobileDevice() {
    const ua = navigator.userAgent;
    const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    const isSmallScreen = window.innerWidth <= 768;
    const isMobileUA = /Mobi|Android|iPhone|iPad|iPod|Phone/i.test(ua);
    return (isMobileUA && hasTouch) || (isSmallScreen && hasTouch);
}
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
    .then(() => console.log('Service Worker registered'))
    .catch(err => console.error('SW registration failed', err));
}