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
    const [bind_element,hideMenu] = register_menu(menu_element, before_open);
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
    $('#BackTop').click(function () {
        $body.scrollTop(0);
    });
    $(window).scroll(function () {
        if ($(this).scrollTop() > 300) {
            $('#BackTop').fadeIn(222);
        } else {
            $('#BackTop').stop().fadeOut(222);
        }
    }).scroll();
    var hash = location.hash;
    let page_cnt = document.querySelectorAll('img').length;
    $("#page").text("0".repeat(Math.floor(Math.log10(page_cnt))) + "1/" + page_cnt);
    if (hash) update_page();

    function update_page() {
        let s = location.hash;
        if (s) {
            s = s.substr(1, s.indexOf("_") - 1);
            $("#page").text(s + "/" + page_cnt);
        }
    }

    var cur = null;

    function onEnterView(entries, observer) {
        for (let entry of entries) {
            if (entry.isIntersecting && entry.intersectionRatio > 0.3) {
                cur = entry.target;
                history.replaceState({}, "", "#" + entry.target.id);
                update_page();
                return;
            }
        }
    }

    const watcher = new IntersectionObserver(onEnterView, {
        threshold: [0.0, 0.25, 0.5, 0.75, 1.0],
    });
    var q = [];

    function action() {
        let img = q.shift();

        let is_error = false;

        function cur() {
            is_error = false;
            let w = Math.floor(1000 * (page_cnt - q.length) / page_cnt);
            $("#loading").text("Loading..." + (Math.floor(w / 10)) + "." + (w % 10) + "%")
            if (hash && ("#" + img.id) == hash) {
                var target_top = $(hash).offset().top;
                $body.scrollTop(target_top);
                hash = null;
            }
            if (q.length) {
                window.setTimeout(function () {
                    action();
                }, 1);
            } else {
                $("#loading").css("display", "none");
            }
            window.setTimeout(function () {
                watcher.observe(img);
            }, 1);
        }

        function retry() {
            if (is_error) {
                is_error = false;
                img.setAttribute('src', img.dataset.src + "?r=" + Math.random());
            }
        }

        img.addEventListener('load', cur);
        img.addEventListener('error', function () {
            is_error = true;
        });
        img.setAttribute('src', img.dataset.src);
        img.addEventListener("click", retry);
        if (img.complete) cur();
    }

    function add(o) {
        q.push(o);
        if (q.length == 1) window.setTimeout(function () {
            action();
        }, 1);
    }

    for (let o of document.querySelectorAll('.img')) add(o);
    var $body = (window.opera) ? (document.compatMode == "CSS1Compat" ? $('html') : $('body')) : $('html,body');
    var lock = false;
    $body.keypress(function (event) {
        event.preventDefault();
        lock = true;
        let code = event.code;
        if (cur) {
            if (code === "Space" || code === "ArrowRight" || code === "ArrowDown" || code === "PageDown" || code === "KeyS" || code === "KeyD") {
                let t = $(cur).next();
                if (t[0]) {
                    cur = t[0];
                    history.replaceState({}, "", "#" + cur.id);
                    var target_top = t.offset().top;
                    $body.scrollTop(target_top);
                }
            }
            if (code === "ArrowLeft" || code === "ArrowUp" || code === "PageUp" || code === "KeyW" || code === "KeyA") {
                let t = $(cur).prev();
                if (t[0]) {
                    cur = t[0];
                    history.replaceState({}, "", "#" + cur.id);
                    var target_top = t.offset().top;
                    $body.scrollTop(target_top);
                }
            }
        }
        return false;
    });
    update_page();
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
    window.history.back();
});