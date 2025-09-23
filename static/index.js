let mobile = isMobileDevice();
let gallery_width = mobile ? "33%" : "16.2%";
const step = 96;
let waiting = true;
let offset = +localStorage.getItem("index_offset") || 0;
let waiting_up = offset > 0;
let end = offset;
const watcher = new IntersectionObserver(onEnterView);
const watcher2 = new IntersectionObserver(onEnterView2);
let up_index = offset;
const menu_element = document.getElementById('custom-menu');
let target_source = "#";
function before_open(e) {
    let gallery = e.closest('.gallery');
    target_source = gallery.dataset.source || "#";
}
document.getElementById("custom-menu-action1").addEventListener('click', () => {
    if (target_source && target_source !== "#") {
        window.open(target_source, '_blank');
    }
    hideMenu();
});
document.getElementById("custom-menu-action2").addEventListener('click', () => {
    location.reload();
});
const [bind_element,hideMenu] = register_menu(menu_element, before_open);

function create_gallery(o) {
    const div = document.createElement('div');
    div.className = 'gallery';
    div.style.width = gallery_width;
    div.dataset.source = o['source'];

    const a = document.createElement('a');
    a.href = '/books/' + o['uid'];

    const innerDiv = document.createElement('div');
    const img = document.createElement('img');
    img.className = 'lazy';
    img.setAttribute('data-src', '/icon/' + o['dirname']);
    innerDiv.appendChild(img);

    const p = document.createElement('p');
    p.textContent = o['title'];

    a.appendChild(innerDiv);
    a.appendChild(p);
    div.appendChild(a);

    bind_element(div);
    return div;
}

function add_end(initial) {
    if (waiting) {
        waiting = false;
        fetch(`/api/index?begin=${end + 1}&count=${step}`)
            .then(response => {
                if (response.status === 401) {
                    window.location.href = "/login";
                    return Promise.reject("Unauthorized");
                }
                if (!response.ok) {
                    window.alert(`錯誤：${response.status} ${response.statusText}`);
                    return Promise.reject(`Error: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                let HEIGHT = Math.floor(document.body.clientWidth / (mobile ? 3 : 6)) + "px";
                // localStorage.setItem("index_offset", end);
                for (let o of data["books"]) {
                    let e = create_gallery(o);
                    let img = e.querySelector("img");
                    e.dataset.pos = end;
                    img.style.height = HEIGHT;
                    watcher.observe(img);
                    watcher2.observe(e);
                    document.getElementById("main_area").appendChild(e);
                    end++;
                }
                if (data["length"]) {
                    waiting = true;
                } else if (initial) {
                    waiting = true;
                    end = 0;
                    offset = 0;
                    add_end();
                }
            })
            .catch(err => {
                if (err !== "Unauthorized") {
                    window.alert("無法取得資料，請稍後再試。\n" + err);
                }
            });
    }
}

function add_start(end_pos) {
    if (waiting_up && end_pos > 0) {
        waiting_up = false;
        let begin = Math.max(0, end_pos - step);
        fetch(`/api/index?begin=${begin + 1}&count=${end_pos - begin}`)
            .then(response => {
                if (response.status === 401) {
                    window.location.href = "/login";
                    return Promise.reject("Unauthorized");
                }
                if (!response.ok) {
                    window.alert(`錯誤：${response.status} ${response.statusText}`);
                    return Promise.reject(`Error: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                let HEIGHT = Math.floor(document.body.clientWidth / (mobile ? 3 : 6)) + "px";
                let old_begin = document.querySelector(".gallery");
                let pos = end_pos - 1;
                for (let i = data["books"].length - 1; i >= 0; i--) {
                    let o = data["books"][i];
                    let e = create_gallery(o);
                    let img = e.querySelector("img");
                    e.dataset.pos = pos;
                    img.style.height = HEIGHT;
                    watcher.observe(img);
                    watcher2.observe(e);
                    document.getElementById("main_area").prepend(e);
                    pos--;
                }
                up_index = begin;
                window.scrollTo(0, old_begin.offsetTop);
                if (begin > 0) {
                    waiting_up = true;
                }
                // localStorage.setItem("index_offset", begin);
            })
            .catch(err => {
                if (err !== "Unauthorized") {
                    window.alert("無法取得資料，請稍後再試。\n" + err);
                }
            });
    }
}

add_end(true);

function onEnterView(entries, observer) {
    const imgs = document.querySelectorAll('img');
    const first_img = imgs[0];
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

function onEnterView2(entries, observer) {
    let res = []
    for (let entry of entries) {
        if (entry.isIntersecting) {
            const e = entry.target;
            let pos = e.dataset.pos;
            res.push(+pos);
        }
    }
    if (res.length === 0) return;
    let mi = Math.min(...res);
    let val = mi - mi%step;
    localStorage.setItem("index_offset", val);
}

function onScroll() {
    let pos = window.scrollY;
    if (up_index > 0 && pos < 10) {
        add_start(up_index);
    }
}

window.addEventListener('scroll', onScroll);