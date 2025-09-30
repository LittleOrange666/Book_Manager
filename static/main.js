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
        let startX, startY;
        target.addEventListener('touchstart', e => {
            longPressTriggered = false;
            startX = e.touches[0].pageX;
            startY = e.touches[0].pageY;
            touchTimer = setTimeout(() => {
                const touch = e.touches[0];
                longPressTriggered = true;
                e.preventDefault();
                showMenu(touch.pageX, touch.pageY, e.target);
            }, 500);
        });
        target.addEventListener('touchmove', e => {
            const touch = e.touches[0];
            const dx = Math.abs(touch.pageX - startX);
            const dy = Math.abs(touch.pageY - startY);
            if (dx > 10 || dy > 10) {
                clearTimeout(touchTimer);
            }
        });
        target.addEventListener('touchend', (e) => {
            clearTimeout(touchTimer);
            if (longPressTriggered) {
                e.preventDefault();
            }
        });
    }

    return [bind_element, hideMenu];
}

function auto_retry(img){
    function handler(){
        const maxRetries = 3;
        let retries = parseInt(img.dataset.retries || '0', 10);
        if (retries < maxRetries) {
            retries += 1;
            img.dataset.retries = retries;
            window.setTimeout(() => {
                const separator = img.src.includes('?') ? '&' : '?';
                img.src = img.src.split('?')[0] + `${separator}t=${new Date().getTime()}`;
            },1500);
        } else {
            img.removeEventListener('error', handler);
        }
    }
    let completed = img.complete;
    if(completed) return;
    img.addEventListener('error', handler);
    img.addEventListener('load', ()=>{
        img.removeEventListener('error', handler);
        completed = true;
    });
    img.addEventListener("click", function (){
        if (!(completed || img.complete)){
            img.dataset.retries = '0';
            img.addEventListener('error', handler);
            handler();
        }
    });
}