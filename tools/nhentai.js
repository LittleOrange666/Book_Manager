// ==UserScript==
// @name         nhentai NEW
// @namespace    http://tampermonkey.net/
// @version      2026-05-11
// @description  try to take over the world!
// @author       You
// @match        https://nhentai.net/*
// @icon         https://nhentai.net/favicon.ico
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    const downloader = "http://127.0.0.1:6756"; // downloader url
    const lang_code = 29963; // key to filter the language of books, chinese = 29963, english = 12227, japanese = 6346
    const admin_key = "<admin key>"; // admin key of downloader
    const originalFetch = window.fetch;
    function is_index(){
        let p = location.pathname;
        return p.startsWith("/tag") || p.startsWith("/artist") || p.startsWith("/group") || p.startsWith("/character") || p.startsWith("/parody") || p.startsWith("/language") || p.startsWith("/favorites") || p==="/";
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
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
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
        let favorite_link = "/api/v2/galleries/"+name+"/favorite"
        let headers = new Headers();
        headers.append("Authorization", auth);
        await fetch(favorite_link, {method: "POST", headers: headers});
        return true;
    }
    function download(link){
        new_download(link).then(function(success){
            if (success) {
                console.log("success");
            } else {
                console.log("error");
            }
        }).catch(function (error){
            console.log(error);
            window.alert("Download Faild, Please check the Downloader");
        });
    }
    function load_gallery(){
        if (document.querySelector("#favorite")){
            let btn = E("button","btn btn-secondary","DoDownload");
            document.querySelector("#favorite").parentElement.appendChild(btn);
            btn.addEventListener("click",function(e){
                e.preventDefault();
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
        let search = new URLSearchParams(location.search);
        search.set("sort","date");
        search.set("page", page);
        to_link("?"+search.toString());
    }
    function random_page(num_pages){
        to_page(Math.ceil(num_pages*Math.random()));
    }
    let prev_page = null;
    function load_index(galleries, page, num_pages){
        let id_mp = {};
        for(let gallery of galleries){
            id_mp[""+gallery.id] = gallery["media_id"];
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
        if(galleries.length===0&&num_pages>1){
            if(sessionStorage.rp){
                random_page(num_pages);
            }else if (page===1){
                to_page(+page+1);
            }else if (page===num_pages){
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
                    random_page(num_pages);
                });
                d1.appendChild(b1);
                document.querySelector(".sort").appendChild(d1);
                if (document.querySelector(".desktop-pagination")){
                    let as = document.querySelectorAll(".desktop-pagination a");
                    let rp = E("a",as[as.length-1].className,"?");
                    rp.onclick = function(){
                        sessionStorage.rp = 1;
                        random_page(num_pages);
                    };
                    document.querySelector(".desktop-pagination").insertBefore(rp,as[as.length-1].nextSibling);
                }
            }
        }
        prev_page = page;
    }
    function get_url(s){
        return s.includes("http")?new URL(s):new URL(location.origin+s);
    }
    let safe_flag = false;
    window.fetch = async (...args) => {
        let request;
        if (args[0] instanceof Request) {
            request = args[0];
        } else {
            request = new Request(args[0], args[1]);
        }
        if (request.method !== "GET") return await originalFetch(request);
        let path = request.url;
        if (path.includes('galleries/tagged')){
            let url = get_url(path);
            url.pathname = "/api/v2/search";
            let tag_id = url.searchParams.get("tag_id");
            if (sessionStorage["tag-"+tag_id]){
                url.searchParams.delete("tag_id");
                url.searchParams.append("query",sessionStorage["tag-"+tag_id]+" language:chinese");
                path = url.href;
                request = new Request(path, request);
                safe_flag = true;
            }
        }
        const response = await originalFetch(request);
        if (path.includes('/search')||path.includes('galleries/tagged')) {
            const data = await response.json();
            let arr = data.result;
            let nw_arr = [];
            for(let gallery of arr){
                if (gallery.tag_ids.includes(lang_code)) {
                    nw_arr.push(gallery);
                }
            }
            data.result = nw_arr;
            let page = Number(get_url(path).searchParams.get("page")||"1");
            let num_pages = data.num_pages;
            window.setTimeout(load_index.bind(null, nw_arr, page, num_pages), 10);
            document.querySelector(".count").textContent = ""+data.total;
            return new Response(JSON.stringify(data), {
                status: response.status,
                statusText: response.statusText,
                headers: response.headers
            });
        }else if (path.match(/galleries\/\d+/)){
            window.setTimeout(load_gallery,10);
        }else if (path.match("tags\/\(.+)\/(.+)")){
            const data = await response.json();
            let o = path.match("tags\/\(.+)\/(.+)");
            if("language"!==o[1])sessionStorage["tag-"+data.id] = o[1]+":"+o[2];
            return new Response(JSON.stringify(data), {
                status: response.status,
                statusText: response.statusText,
                headers: response.headers
            });
        }
        return response;
    };
    window.setTimeout(function(){
        if(is_index()){
            let search = new URLSearchParams(location.search);
            if(!search.get("page")&&!safe_flag) to_page(1);
        }
        load_gallery();
    },100);
})();