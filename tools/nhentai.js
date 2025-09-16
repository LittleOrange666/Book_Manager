// ==UserScript==
// @name         nhentai
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  try to take over the world!
// @author       You
// @match        https://nhentai.net/*
// @icon         https://nhentai.net/favicon.ico
// @grant        none
// ==/UserScript==
(function() {
    'use strict';
    const downloader = "http://127.0.0.1:6756"; // downloader url
    const min_pages = 15; // random will skip books that less than [min_pages] pages
    const lang_code = "29963"; // key to filter the language of books, chinese = 29963, english = 12227, japanese = 6346
    const random_buffer = 10;
    const admin_key = "your_admin_key"; // admin key of downloader
    function pure(s){
        while (s.indexOf("[")!=-1){
            let i = s.indexOf("[");
            let j = s.indexOf("]");
            s = s.substring(0,i) + s.substring(j+1,s.length);
        }
        return s;
    }
    function gettargets(){
        let r = sessionStorage.targets.split(",");
        while (r.length&&(!r[0]))r = r.splice(1);
        return r;
    }
    function settargets(v){
        sessionStorage.targets = v.toString();
    }
    async function new_download(link){
        if (!link) link = location.href;
        if (!link.endsWith("/")) link += "/";
        let name = link.substring(22,28);
        let res1 = await fetch(link+"download");
        if (!res1.ok) {
            window.alert("Failed to download torrent");
            return false;
        }
        let blob = await res1.blob();
        let form = new FormData();
        form.append("source", link);
        form.append("admin_key", admin_key);
        form.append("uid","book_"+name);
        form.append("file", blob, name+".torrent");
        let res2 = await fetch(downloader+'/api/book', {
            method: "POST",
            body: form
        });
        if (!res2.ok) {
            window.alert("Failed to upload torrent");
            return false;
        }
        if (res2.status !== 200) {
            let data = await res2.text();
            window.alert(data);
            return false;
        }
        return true;
    }
    function download(link, callback, error_callback){
        new_download(link).then(function(success){
            if (success) {
                if (sessionStorage.isr && location.pathname.startsWith("/g")) {
                    applyrandom();
                }
                if (callback instanceof Function) callback();
            } else {
                if (error_callback instanceof Function) error_callback();
            }
        }).catch(function (error){
            console.log(error);
            window.alert("Download Faild, Please check the Downloader");
            if (error_callback instanceof Function) error_callback();
        });
    }
    function E(t,c,i){
        let r = document.createElement(t);
        if (c) r.className = c;
        if (i) r.textContent = i;
        return r;
    }
    function httpGet(theUrl){
        console.log(theUrl);
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open( "GET", theUrl, false );
        xmlHttp.send( null );
        return xmlHttp.responseText;
    }
    function span(L, i){
        if (!i) {
            message("Continuous downloading(0/"+L.length+")","Please wait");
            i = 0;
        }else{
            setmessage("Continuous downloading("+i+"/"+L.length+")","Please wait");
        }
        download(L[i],function(){
            if (L.length>i+1){
                span(L,i+1);
            }else{
                stopmessage();
            }
        },stopmessage);
    }
    function message(first, second){
        const contentChildren = document.querySelectorAll("#content > *");
        contentChildren.forEach(el => el.style.display = "none");
        const div = document.createElement("div");
        div.className = "container error";
        const h1 = document.createElement("h1");
        h1.id = "first_message";
        h1.textContent = first;
        const p = document.createElement("p");
        p.id = "second_message";
        p.textContent = second;
        div.appendChild(h1);
        div.appendChild(p);
        document.querySelector("#content").appendChild(div);
    }
    function setmessage(first, second){
        document.querySelector("#first_message").textContent = first;
        document.querySelector("#second_message").textContent = second;
    }
    function stopmessage(){
        const errorDiv = document.querySelector("#content div.container.error");
        if (errorDiv) errorDiv.remove();
        const contentChildren = document.querySelectorAll("#content > *");
        contentChildren.forEach(function(el) {
            el.style.display = "block";
        });
    }
    // random functions
    async function dorandom(){
        let it;
        function inner(){
            let tp = Math.ceil(sessionStorage.randomCnt*Math.random());
            let target = location.origin+sessionStorage.randomType+"?page="+tp;
            let s = httpGet(target);
            let i = 0;
            let l = []
            while (true){
                let j = s.indexOf("<div class=\"gallery\" ",i);
                if (j==-1) break;
                let k = s.indexOf("a href=",j);
                let kk = s.indexOf(lang_code,j);
                i = k+11;
                if (kk!=-1&&kk<k){
                    let ed = s.indexOf("/",i);
                    let idx = s.substring(i,ed);
                    l.push(idx);
                }
            }
            console.log(l);
            if (l.length>0){
                let target_url = "https://nhentai.net/g/"+l[Math.floor(Math.random()*l.length)]+"/";
                console.log(target_url);
                let targets = gettargets();
                targets.push(target_url);
                settargets(targets);
                if (targets.length>=random_buffer) window.clearInterval(it);
            }else{
                console.log("faild");
            }
        }
        let targets = gettargets();
        if (targets.length<random_buffer){
            it = window.setInterval(inner,5000);
        }
    }
    async function runrandom(){
        let hr;
        if(document.querySelector(".last")){
            hr = document.querySelector(".last").href;
        }else{
            let pl = document.querySelectorAll(".page");
            hr = pl[pl.length-1].href;
        }
        let cnt = Number(hr.substring(hr.indexOf("page=")+5));
        sessionStorage.randomCnt = cnt;
        sessionStorage.randomType = location.pathname;
        return await dorandom();
    }
    var applied_random = false;
    function applyrandom(){
        if (!applied_random){
            applied_random = true;
            let targets = gettargets();
            if(targets.length){
                let target = targets[0];
                targets = targets.splice(1);
                settargets(targets);
                sessionStorage.isr = 1;
                sessionStorage.simply = 1;
                location.href = target;
            }else{
                message("Finding random","Please wait");
                var it;
                it = window.setInterval(function(){
                    let targets = gettargets();
                    if(targets.length) {
                        window.clearInterval(it);
                        let target = targets[0];
                        targets = targets.splice(1);
                        settargets(targets);
                        sessionStorage.isr = 1;
                        sessionStorage.simply = 1;
                        location.href = target;
                    }
                },100);
            }
        }
    }
    // general
    for(let o of document.querySelectorAll("iframe")){
        o.remove();
    }
    for(let o of document.querySelectorAll(".advertisement")){
        o.remove();
    }
    {
        let li = E("li","desktop"+(location.pathname.startsWith("/input")?" active":""));
        let a = E("a","","Input");
        a.setAttribute("href","/input/");
        li.appendChild(a);
        document.querySelector(".menu.left").insertBefore(li,document.querySelector(".menu.left").children[7]);
    }
    // pages
    if(location.pathname.startsWith("/tag")||location.pathname.startsWith("/artist")||location.pathname.startsWith("/group")||location.pathname.startsWith("/character")||location.pathname.startsWith("/parody")||location.pathname.startsWith("/language")||location.pathname.startsWith("/favorites")||location.pathname=="/"){
        if (document.querySelectorAll("h3").length==0){
            for(let o of document.querySelectorAll('.gallery[data-tags*="'+lang_code+'"]')) o.isch = 1;
            for(let o of document.querySelectorAll('.gallery')) if(!o.isch)o.remove();
            if (document.querySelectorAll('.gallery').length==0){
                if (document.querySelector(".previous")==null) location.href = document.querySelector(".next").href;
                else if (document.querySelector(".next")==null) location.href = document.querySelector(".previous").href;
                else if(document.referrer&&document.referrer.startsWith(location.origin+location.pathname)){
                    let p = 1;
                    if (document.referrer.indexOf("page")!=-1)p = +document.referrer.substr(document.referrer.indexOf("page")+5);
                    let cp = +location.search.substr(6);
                    if(Math.abs(p-cp)==1) location.search = "?page="+(cp*2-p);
                }
            }else{
                if (document.querySelector(".sort")){
                    let l = [];
                    for(let o of document.querySelectorAll(".gallery")){
                        l.push(o.childNodes[0].href);
                    }
                    let d = E("div","sort-type");
                    let b = E("a","current","Download All");
                    b.onclick = function(){
                        span(l);
                    };
                    d.appendChild(b);
                    document.querySelector(".sort").appendChild(d);
                    let d0 = E("div","sort-type");
                    let b0 = E("a","current","Random");
                    settargets([]);
                    runrandom();
                    b0.onclick = function(){
                        applyrandom();
                    };
                    d0.appendChild(b0);
                    document.querySelector(".sort").appendChild(d0);
                }
            }
            for(let o of document.querySelectorAll('.gallery')){
                let a = document.createElement("a");
                let link = o.querySelector("a").href;
                a.onclick = function(){
                    download(link);
                };
                a.appendChild(o.querySelector("div"));
                o.appendChild(a);
            }
        }
    }
    if(location.pathname.startsWith("/g")){
        document.querySelector("#comment-post-container").remove();
        document.querySelector("#comment-container").remove();
        document.querySelector("#download").onclick = function(){return false;};
        document.querySelector("#download").addEventListener("click",function(){
            if(document.querySelector("#favorite span").textContent=="Favorite") document.querySelector("#favorite").click();
            download();
        });
        if (sessionStorage.isr){
            let s = sessionStorage.randomType;
            s = s.substring(1,s.length-1).replaceAll("/",":").replaceAll("-"," ");
            let b = E("a","btn btn-secondary", "Next Random("+s+")");
            dorandom();
            b.onclick = function(){
                applyrandom();
            };
            document.querySelector(".buttons").appendChild(b);
            if(sessionStorage.simply){
                delete sessionStorage.simply;
                document.querySelector("#related-container").remove();
            }
            let pc = Number(document.querySelectorAll("#tags div span.name")[7].textContent);
            if (pc<min_pages) applyrandom();
        }
    }else{
        delete sessionStorage.isr;
    }
    if(location.pathname.startsWith("/input")){
        document.querySelector("title").textContent = 'Code Input » nhentai: hentai doujinshi and manga';
        let con = document.querySelector("#content");
        con.removeChild(con.firstElementChild);
        (function(){
            let d0 = E("div","container");
            let d1 = E("div","row");
            let d2 = E("div");
            let h = E("h3","","Input Cookie");
            let b = E("button","btn btn-primary","Save");
            let t = E("textarea");
            d2.appendChild(b);
            d1.appendChild(t);
            d1.appendChild(d2);
            d0.appendChild(h);
            d0.appendChild(d1);
            con.appendChild(d0);
            t.setAttribute("placeholder","Input cookie here");
            b.onclick = function(){
                let s = t.value;
                localStorage.THE_COOKIE = s;
                window.alert("Cookie Saved")
            };
        })();
        (function(){
            let d0 = E("div","container");
            let d1 = E("div","row");
            let d2 = E("div");
            let h = E("h3","","Input Codes");
            let b = E("button","btn btn-primary","Submit");
            let t = E("textarea");
            d2.appendChild(b);
            d1.appendChild(t);
            d1.appendChild(d2);
            d0.appendChild(h);
            d0.appendChild(d1);
            con.appendChild(d0);
            t.setAttribute("placeholder","Input codes here, one code per line");
            b.onclick = function(){
                let s = t.value;
                let l = s.split("\n");
                l = l.filter(s=>(typeof s == "string")&&s);
                l = l.map(s=>"https://nhentai.net/g/"+s);
                console.log(l);
                if(l) span(l);
            };
        })();
    }
})();