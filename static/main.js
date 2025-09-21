function isMobileDevice() {
    const ua = navigator.userAgent;
    const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    const isSmallScreen = window.innerWidth <= 768;
    const isMobileUA = /Mobi|Android|iPhone|iPad|iPod|Phone/i.test(ua);
    return (isMobileUA && hasTouch) || (isSmallScreen && hasTouch);
}

function isRunningStandalone() {
    return (
        window.navigator.standalone === true ||
        window.matchMedia('(display-mode: standalone)').matches
    );
}

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
        .then(() => console.log('Service Worker registered'))
        .catch(err => console.error('SW registration failed', err));
}

function register_menu(menu_element, before_open) {
    function showMenu(x, y, e) {
        before_open(e);
        menu_element.style.left = `${x}px`;
        menu_element.style.top = `${y}px`;
        menu_element.style.display = 'block';
    }

    function hideMenu() {
        menu_element.style.display = 'none';
    }

    document.addEventListener('click', e => {
        if (!menu_element.contains(e.target)) hideMenu();
    });

    function bind_element(target) {
        target.addEventListener('contextmenu', e => {
            e.preventDefault();
            showMenu(e.pageX, e.pageY, e.target);
        });
        let touchTimer;
        let longPressTriggered = false;
        target.addEventListener('touchstart', e => {
            longPressTriggered = false;
            touchTimer = setTimeout(() => {
                e.preventDefault();
                longPressTriggered = true;
                const touch = e.touches[0];
                showMenu(touch.pageX, touch.pageY, e.target);
            }, 500);
        });
        target.addEventListener('touchend', (e) => {
            clearTimeout(touchTimer);
            if (longPressTriggered) {
                e.preventDefault();
            }
        });
    }
    return [bind_element,hideMenu];
}