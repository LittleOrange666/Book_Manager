function main(data) {
    let mobile = isMobileDevice();
    const menu_element = document.getElementById('custom-menu');
    function before_open(e) {
        // placeholder
    }
    document.getElementById("custom-menu-action1").addEventListener('click', () => {
        let source = data["source"];
        if (source) {
            window.open(source, '_blank');
        }
    });
    document.getElementById("custom-menu-action2").addEventListener('click', () => {
        location.reload();
    });
    const [bind_element, hideMenu] = register_menu(menu_element, before_open);
    bind_element(document.querySelector("#main_area"));

    if (!mobile) {
        const base_zoom = Math.max(Math.floor(window.devicePixelRatio || 1), 1);

        function updateLayout() {
            const zoom = (window.devicePixelRatio || 1) / base_zoom;
            const contentPercent = zoom * 30;
            const contentWidth = Math.min(100, Math.max(10, contentPercent));
            const marginPercent = (100 - contentWidth) / 2;
            const mainContent = document.querySelector('#main_area');
            mainContent.style["margin-left"] = `${marginPercent}%`;
            mainContent.style["margin-right"] = `${marginPercent}%`;
        }

        updateLayout();

        window.addEventListener('resize', updateLayout);
    } else if (isRunningStandalone()) {
        document.querySelector("#bottom_area").style.paddingBottom = "30px";
    }

    var $body = (window.opera) ? (document.compatMode == "CSS1Compat" ? $('html') : $('body')) : $('html,body');

    $('#BackTop').click(function () {
        $body.scrollTop(0);
        window.scrollTo(0, 0);
    });
    $(window).scroll(function () {
        if ($(this).scrollTop() > 300) {
            $('#BackTop').fadeIn(222);
        } else {
            $('#BackTop').stop().fadeOut(222);
        }
    }).scroll();

    let book_uid = location.pathname.split("/").pop();
    let initial_hash = location.hash ? location.hash.substring(1) : "";
    let saved_pos = localStorage.getItem("book_pos_" + book_uid) || "";
    let target_id = initial_hash || saved_pos;

    let page_cnt = document.querySelectorAll('img').length;
    $("#page").text("0".repeat(Math.floor(Math.log10(page_cnt))) + "1/" + page_cnt);

    function update_page() {
        let id = cur ? cur.id : (location.hash ? location.hash.substring(1) : "");
        if (id && id.includes("_")) {
            let pageStr = id.substring(0, id.indexOf("_"));
            $("#page").text(pageStr + "/" + page_cnt);
        }
    }

    var cur = null;

    function onEnterView(entries, observer) {
        for (let entry of entries) {
            if (entry.isIntersecting && entry.intersectionRatio > 0.3) {
                cur = entry.target;
                history.replaceState({}, "", "#" + entry.target.id);
                localStorage.setItem("book_pos_" + book_uid, entry.target.id);
                update_page();
                return;
            }
        }
    }

    const watcher = new IntersectionObserver(onEnterView, {
        threshold: [0.0, 0.25, 0.5, 0.75, 1.0],
    });

    function scrollToElement(el) {
        if (!el) return;
        requestAnimationFrame(() => {
            const targetTop = $(el).offset().top;
            $body.scrollTop(targetTop);
            window.scrollTo(0, targetTop);
        });
    }

    var q = [];

    function action() {
        if (q.length === 0) {
            $("#loading").css("display", "none");
            return;
        }

        let img = q.shift();
        let stepDone = false;

        function cur_step() {
            if (stepDone) return;
            stepDone = true;

            let loaded_cnt = page_cnt - q.length;
            let w = Math.floor(1000 * loaded_cnt / page_cnt);
            $("#loading").text("Loading..." + (Math.floor(w / 10)) + "." + (w % 10) + "%");

            if (target_id && img.id === target_id) {
                scrollToElement(img);
                target_id = null;
            }

            if (q.length) {
                window.setTimeout(action, 1);
            } else {
                $("#loading").css("display", "none");
            }

            window.setTimeout(() => {
                watcher.observe(img);
            }, 1);
        }

        img.addEventListener('load', () => {
            if (target_id && img.id === target_id) {
                scrollToElement(img);
                target_id = null;
            }
            cur_step();
        });

        // Ensure errors move the queue forward so remaining images can load
        img.addEventListener('error', cur_step);

        auto_retry(img);
        img.setAttribute('src', img.dataset.src);

        if (img.complete) {
            cur_step();
        }
    }

    function add(o) {
        q.push(o);
        if (q.length === 1) {
            window.setTimeout(action, 1);
        }
    }

    for (let o of document.querySelectorAll('.img')) add(o);

    $(document).on('keydown', function (event) {
        let code = event.code;
        if (cur) {
            if (code === "Space" || code === "ArrowRight" || code === "ArrowDown" || code === "PageDown" || code === "KeyS" || code === "KeyD") {
                event.preventDefault();
                let t = $(cur).next('.img');
                if (t[0]) {
                    cur = t[0];
                    history.replaceState({}, "", "#" + cur.id);
                    localStorage.setItem("book_pos_" + book_uid, cur.id);
                    update_page();
                    scrollToElement(cur);
                }
            }
            if (code === "ArrowLeft" || code === "ArrowUp" || code === "PageUp" || code === "KeyW" || code === "KeyA") {
                event.preventDefault();
                let t = $(cur).prev('.img');
                if (t[0]) {
                    cur = t[0];
                    history.replaceState({}, "", "#" + cur.id);
                    localStorage.setItem("book_pos_" + book_uid, cur.id);
                    update_page();
                    scrollToElement(cur);
                }
            }
        }
    });

    if (target_id) {
        update_page();
    }
}

let book_uid = location.pathname.split("/").pop();

fetch("/api/book?uid=" + book_uid)
    .then(response => response.json())
    .then(data => {
        if (!data["message"]) {
            document.title = data["title"];
            let source = data["source"];
            let files = data["files"];
            let dirname = data["dirname"];
            let area = $("#main_area");
            for (let file of files) {
                let img = $("<img class='img lazy' id='" + file.replaceAll(".", "_") + "' data-src='/image/" + dirname + "/" + file + "'>");
                area.append(img);
            }
            if (source) {
                let e = $('<p class="source"><a href="' + source + '" class="source" target="_blank">Source</a></p><p class="source"></p>');
                area.append(e);
            }
            main(data);
        } else {
            alert("Error: " + data["message"]);
        }
    })
    .catch(error => {
        alert("Error: " + error);
    });

$("#home-link").click(function () {
    location.replace("/");
});