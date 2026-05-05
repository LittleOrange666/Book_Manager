import hashlib
import math
import os
import shutil
import time
import traceback

import bencodepy
import qbittorrentapi
import requests
from loguru import logger
from PIL import Image

from . import datas, constants, server

conn_info = {
    "host": os.environ.get("WEBUI_HOST", "localhost"),
    "port": int(os.environ.get("WEBUI_PORT", "8082")),
    "username": os.environ.get("WEBUI_USER", "admin"),
    "password": os.environ.get("WEBUI_PASS", "adminmeow")
}
qbt_client = qbittorrentapi.Client(**conn_info)


def init():
    try:
        qbt_client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        print(e)
        return False
    return True


def convert_to_ico(input_path, output_path, size=256):
    img = Image.open(input_path)
    img = img.convert("RGBA")
    img.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    x = (size - img.width) // 2
    y = (size - img.height) // 2
    canvas.paste(img, (x, y), img)
    canvas.save(output_path, format="ICO")
    logger.debug(f"created ico file from {input_path!r} to {output_path!r}")


def resolve(dbsession, uid):
    info = dbsession.query(datas.Book).filter_by(uid=uid).first()
    info.completed = True
    path = constants.book_path / info.dirname
    if path.exists() and path.is_dir():
        inner_dir = list(path.iterdir())[0]
        for f in inner_dir.iterdir():
            shutil.move(str(f), str(path / f.name))
        inner_dir.rmdir()
        files = [f for f in path.iterdir() if f.suffix[1:].lower() in constants.exts]
        files.sort(key=lambda x: x.stem)
        if files:
            icon_file = files[0].name
            convert_to_ico(path / icon_file, path / "icon.ico")
    logger.info(f"Complete downloading {info.title} - {uid}")
    dbsession.add(info)

def do_download(download: datas.Download, dbsession) -> bool:
    res = requests.post(download.link, headers={"Authorization": download.auth})
    if res.status_code != 200:
        logger.info(f"Failed to download torrent info for {download.title} - {download.uid}: HTTP {res.status_code}")
        return False
    dat = res.json()
    url1 = dat["url"]
    res2 = requests.get(url1)
    if res2.status_code != 200:
        logger.info(f"Failed to download torrent file for {download.title} - {download.uid}: HTTP {res2.status_code}")
        return False
    start_download(file_content=res2.content, title=download.title, uid=download.uid, dirname=download.dirname,source=download.source, dbsession=dbsession)
    return True

def background_worker():
    with server.app.app_context():
        while True:
            try:
                with datas.SessionContext() as dbsession:
                    uids = []
                    cnt = 0
                    for book in dbsession.query(datas.Book).filter_by(completed=False).all():
                        cnt += 1
                        try:
                            torrent = qbt_client.torrents_info(hashes=book.torrent_hash)
                            if torrent and torrent[0].state in ['uploading', 'pausedUP', 'queuedUP', 'stalledUP',
                                                                'checkingUP']:
                                qbt_client.torrents_delete(hashes=book.torrent_hash)
                                uids.append(book.uid)
                        except Exception as e:
                            logger.error(f"Error checking torrent status for {book.title} - {book.uid}: {e}")
                    for uid in uids:
                        cnt -= 1
                        resolve(dbsession, uid)
                    if uids:
                        if cnt > 0:
                            logger.info(f"{cnt} downloads remaining.")
                        else:
                            logger.info("All downloads completed.")
            except Exception as e:
                traceback.print_exception(e)
            try:
                with datas.SessionContext() as dbsession:
                    nxt = math.floor(time.time() + 360)
                    cur = math.floor(time.time())
                    uids = []
                    cnt = 0
                    bad = False
                    for download in dbsession.query(datas.Download).all():
                        cnt += 1
                        if download.wait > cur:
                            bad = True
                            continue
                        if bad:
                            continue
                        res = do_download(download, dbsession)
                        if res:
                            uids.append(download.uid)
                        else:
                            download.wait = nxt
                            dbsession.add(download)
                            bad = True
                    for uid in uids:
                        cnt -= 1
                        dbsession.delete(dbsession.query(datas.Download).filter_by(uid=uid).first())
                    if uids:
                        if cnt > 0:
                            logger.info(f"{cnt} download infos remaining.")
                        else:
                            logger.info("All download infos completed.")
            except Exception as e:
                traceback.print_exception(e)
            time.sleep(10)


def calculate_torrent_hash(torrent_bytes: bytes) -> str:
    try:
        torrent_data = bencodepy.decode(torrent_bytes)
        info_data = bencodepy.encode(torrent_data[b'info'])
        info_hash = hashlib.sha1(info_data).hexdigest().upper()
        return info_hash
    except Exception as e:
        raise Exception(f"Failed to calculate torrent hash: {e}")


def extract_torrent_title(torrent_bytes):
    try:
        torrent_data = bencodepy.decode(torrent_bytes)
        info = torrent_data.get(b'info', {})
        title = info.get(b'name')
        if not title:
            raise ValueError("Torrent file does not contain a 'name' field.")
        return title.decode('utf-8')
    except bencodepy.exceptions.BencodeDecodeError as e:
        raise ValueError(f"Failed to decode torrent file: {e}")
    except Exception as e:
        raise ValueError(f"Error extracting title: {e}")


def start_download(file_content: bytes, title: str, uid: str, dirname: str, source: str, dbsession = None):
    session = datas.db.session if dbsession is None else dbsession
    old = session.query(datas.Book).filter_by(uid=uid).first()
    if old:
        if old.completed:
            path = constants.book_path / old.dirname
            if path.exists() and path.is_dir():
                logger.info(f"Removing old one {old.title} - {uid}")
                shutil.rmtree(path)
        else:
            try:
                qbt_client.torrents_delete(delete_files=True, hashes=old.torrent_hash)
            except Exception as e:
                logger.error(f"Error deleting old torrent for {old.title} - {uid}: {e}")
        session.delete(old)
        session.flush()
    hash_val = calculate_torrent_hash(file_content)
    res = qbt_client.torrents_add(torrent_files=file_content, save_path=str(constants.inner_book_path / dirname))
    if res != "Ok.":
        logger.error(f"Failed to add torrent for {title} - {uid}: {res}")
        return
    if not title:
        try:
            title = extract_torrent_title(file_content)
        except Exception as e:
            logger.error(f"Failed to extract title from torrent for {uid}: {e}")
            return
    if not hash_val:
        logger.error(f"Failed to retrieve torrent hash for {title} - {uid}")
        return
    logger.debug(f"Torrent hash for {title} - {uid}: {hash_val}")
    if constants.seed_valid:
        filepath = constants.seed_path / f"{uid}.torrent"
        with open(filepath, "wb") as f:
            f.write(file_content)
        logger.debug(f"Saved torrent file to {filepath}")
    dat = datas.Book(uid=uid, title=title, dirname=dirname, completed=False, source=source, torrent_hash=hash_val)
    session.add(dat)
    if dbsession is None:
        datas.db.session.commit()
    else:
        session.flush()

def prepare_download(title: str, uid: str, dirname: str, source: str, auth: str, link: str):
    old = datas.Download.query.filter_by(uid=uid).first()
    if old:
        datas.db.session.delete(old)
        datas.db.session.flush()
    old = datas.Book.query.filter_by(uid=uid).first()
    if old:
        if old.completed:
            path = constants.book_path / old.dirname
            if path.exists() and path.is_dir():
                logger.info(f"Removing old one {old.title} - {uid}")
                shutil.rmtree(path)
        else:
            try:
                qbt_client.torrents_delete(delete_files=True, hashes=old.torrent_hash)
            except Exception as e:
                logger.error(f"Error deleting old torrent for {old.title} - {uid}: {e}")
        datas.db.session.delete(old)
        datas.db.session.flush()
    logger.debug(f"Prepared download for {title} - {uid}, source: {source}")
    if title is None:
        title = ""
    dat = datas.Download(uid=uid, title=title, dirname=dirname, source=source, auth=auth, link=link,
                         wait=math.floor(time.time()-10))
    datas.db.session.add(dat)
    datas.db.session.commit()