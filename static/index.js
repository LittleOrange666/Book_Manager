function isMobileDevice() {
    const ua = navigator.userAgent;
    const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    const isSmallScreen = window.innerWidth <= 768;
    const isMobileUA = /Mobi|Android|iPhone|iPad|iPod|Phone/i.test(ua);
    return (isMobileUA && hasTouch) || (isSmallScreen && hasTouch);
}

let mobile = isMobileDevice();
let gallery_width = mobile ? "33%" : "16.2%";
const step = 100;
let waiting = true;
let end = 0;
const watcher = new IntersectionObserver(onEnterView);

function add_end() {
    if (waiting) {
        waiting = false;
        $.get("/api/index", {"begin": "" + (end + 1), "count": "" + (step)}, function (data, status) {
            let HEIGHT = Math.floor(document.body.clientWidth / (mobile ? 3 : 6)) + "px";
            for (let o of data["books"]) {
                let e = $("<div class='gallery' style='width:" + gallery_width + "'><a href='/books/" + o["uid"] + "'><div><img class='lazy' data-src='/icon/" + o["dirname"] + "'></div><p>" + o["title"] + "</p></a></div>");
                let img = e.find("img");
                img.css("height", HEIGHT);
                watcher.observe(img[0]);
                $("#main_area").append(e);
            }
            if (data["length"]) {
                end += step;
                waiting = true;
            }
        });
    }
}

add_end();

function onEnterView(entries, observer) {
    const imgs = document.querySelectorAll('img');
    const last_img = imgs[imgs.length - 1];
    for (let entry of entries) {
        if (entry.isIntersecting) {
            const img = entry.target;
            img.setAttribute('src', img.dataset.src);
            img.removeAttribute('data-src');
            img.removeAttribute('style');
            observer.unobserve(img);
            if (img === last_img) add_end();
        }
    }
}