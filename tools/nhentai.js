// ==UserScript==
// @name         nhentai NEW
// @namespace    http://tampermonkey.net/
// @version      2026-03-30
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
    const lang_code = 29963; // key to filter the language of books, chinese = 29963, english = 12227, japanese = 6346
    const random_buffer = 10;
    const admin_key = "<admin key>"; // admin key of downloader
    const originalFetch = window.fetch;
    function is_index(){
        let p = location.pathname;
        return p.startsWith("/tag") || p.startsWith("/artist") || p.startsWith("/group") || p.startsWith("/character") || p.startsWith("/parody") || p.startsWith("/language") || p.startsWith("/favorites") || p=="/";
    }
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
    function E(t,c,i){
        let r = document.createElement(t);
        if (c) r.className = c;
        if (i) r.textContent = i;
        return r;
    }
    function getCookie(name) {
        let nameEQ = name + "=";
        let ca = document.cookie.split(';');
        for(let i=0; i < ca.length; i++) {
            let c = ca[i].trim();
            if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }
    function getAuthorization(){
        let token = getCookie("access_token");
        if (!token){
            window.alert("Login Required");
            throw new Error("Login Required;");
        }
        return "User " + token;
    }
    async function new_download(link){
        if (!link) link = location.href;
        if (!link.endsWith("/")) link += "/";
        let name = link.substring(link.indexOf("/g/")+3,link.indexOf("/",link.indexOf("/g/")+4));
        let auth = getAuthorization();
        let api_link = location.origin + "/api/v2/galleries/"+name+"/download?format=torrent"
        let form = new FormData();
        form.append("source", link);
        form.append("admin_key", admin_key);
        form.append("uid","book_"+name);
        form.append("auth",auth);
        form.append("link",api_link);
        let res2 = await fetch(downloader+'/api/book/prepare', {
            method: "POST",
            body: form
        });
        if (!res2.ok) {
            window.alert("Failed to upload torrent info");
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
    function load_gallery(){
        if (document.querySelector("#favorite")){
            let btn = E("button","btn btn-secondary","DoDownload");
            document.querySelector("#favorite").parentElement.appendChild(btn);
            btn.addEventListener("click",function(e){
                e.preventDefault();
                if(document.querySelector("#favorite span").textContent=="Favorite") document.querySelector("#favorite").click();
                download();
            });
        }
    }
    function to_link(link){
        let a = document.createElement("a");
        a.href = link;
        a.style.display = 'none';
        document.body.appendChild(a);
        const clickEvent = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true
        });
        a.dispatchEvent(clickEvent);
        a.remove();
    }
    function to_page(page){
        console.log(page);
        let search = new URLSearchParams(location.search);
        search.set("sort","date");
        search.set("page", page);
        console.log(search.toString());
        to_link("?"+search.toString());
    }
    function randompage(num_pages){
        to_page(Math.ceil(num_pages*Math.random()));
    }
    let prev_page = null;
    function load_index(galleries, page, num_pages){
        let id_mp = {};
        for(let gallery of galleries){
            id_mp[""+gallery.id] = gallery.media_id;
        }
        for(let o of document.querySelectorAll('.gallery')){
            let a0 = o.querySelector("a");
            let img = o.querySelector("img");
            let id = a0.href.match(/\d+/)[0];
            let mid = id_mp[id];
            img.src = img.src.replace(/\d{2,}/,mid);
            let a = document.createElement("a");
            let link = o.querySelector("a").href;
            a.onclick = function(){
                download(link);
            };
            a.appendChild(o.querySelector("div"));
            o.appendChild(a);
        }
        if(galleries.length==0){
            console.log(page, num_pages);
            if(sessionStorage.rp){
                randompage(num_pages);
            }else if (page==1){
                to_page(+page+1);
            }else if (page==num_pages){
                to_page(+page-1);
            }else if(page<prev_page){
                to_page(+page-1);
            }else if (page>prev_page) {
                to_page(+page+1);
            }
        }else {
            delete sessionStorage.rp;
            if (!document.querySelector(".custom-btn-1")){
                let d1 = E("div","sort-type");
                let b1 = E("a","current custom-btn-1","Random Page");
                b1.addEventListener("click",function(){
                    sessionStorage.rp = 1;
                    randompage(num_pages);
                });
                d1.appendChild(b1);
                document.querySelector(".sort").appendChild(d1);
            }
        }
        prev_page = page;
    }
    window.fetch = async (...args) => {
        const response = await originalFetch(...args);
        if (args[0].includes('galleries/tagged')||args[0].includes('galleries/popular')||args[0].includes('galleries?')) {
            const data = await response.json();
            let arr = data.result;
            let nw_arr = [];
            for(let gallery of arr){
                if (gallery.tag_ids.includes(lang_code)) {
                    nw_arr.push(gallery);
                }
            }
            data.result = nw_arr;
            //console.log(args);
            console.log(location.href);
            console.log(location.origin+args[0]);
            let page = Number((new URL(location.origin+args[0])).searchParams.get("page")||"1");
            //console.log(page);
            let num_pages = data.num_pages;
            window.setTimeout(load_index.bind(null, nw_arr, page, num_pages), 10);
            return new Response(JSON.stringify(data), {
                status: response.status,
                statusText: response.statusText,
                headers: response.headers
            });
        }else if (args[0].match(/galleries\/\d+/)){
            window.setTimeout(load_gallery,10);
        }
        return response;
    };
    window.setTimeout(function(){
        if(is_index()){
            let search = new URLSearchParams(location.search);
            if(!search.get("page")) to_page(1);
        }
    },100);
})();