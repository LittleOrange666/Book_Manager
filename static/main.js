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
        .then((reg) => {
            console.log('Service Worker registered');
            reg.update();
        })
        .catch(err => console.error('SW registration failed', err));
}

function register_menu(menu_element, before_open) {
    function showMenu(x, y, e) {
        before_open(e);
        menu_element.style.left = `${x}px`;
        menu_element.style.top = `${y + 15}px`;
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

        target.addEventListener('click', e => {
            if (longPressTriggered) {
                e.preventDefault();
                e.stopPropagation();
                longPressTriggered = false; // Reset after handling
            }
        });

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

function auto_retry(img) {
    let completed = false;

    function handler() {
        if (completed) return;
        const maxRetries = 3;
        let retries = parseInt(img.dataset.retries || '0', 10);
        if (retries < maxRetries) {
            retries += 1;
            img.dataset.retries = retries;
            window.setTimeout(() => {
                if (completed) return;
                const srcBase = img.dataset.src || (img.src ? img.src.split('?')[0] : '');
                if (!srcBase) return;
                const separator = srcBase.includes('?') ? '&' : '?';
                img.src = srcBase + `${separator}t=${Date.now()}`;
            }, 1500);
        } else {
            img.classList.add('img-error');
            img.alt = "Failed to load. Click to retry.";
            img.title = "Click to retry loading";
        }
    }

    img.addEventListener('error', handler);

    img.addEventListener('load', () => {
        if (img.naturalWidth > 0) {
            completed = true;
            img.classList.remove('img-error');
            img.removeAttribute('title');
        }
    });

    img.addEventListener("click", function () {
        if (!completed || img.naturalWidth === 0) {
            completed = false;
            img.dataset.retries = '0';
            img.classList.remove('img-error');
            const srcBase = img.dataset.src || (img.src ? img.src.split('?')[0] : '');
            if (!srcBase) return;
            const separator = srcBase.includes('?') ? '&' : '?';
            img.src = srcBase + `${separator}t=${Date.now()}`;
        }
    });
}