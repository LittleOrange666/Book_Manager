import hashlib
import io
import math
import os
import re
import shutil
import time
from collections import defaultdict
from typing import Literal
from zipfile import ZipFile

import bencodepy
import qbittorrentapi
import requests
from PIL import Image
from loguru import logger
from qbittorrentapi import TorrentState
from sqlalchemy.orm import Session

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
    auth = download.auth
    if os.getenv("DOWNLOAD_AUTH"):
        logger.info(f"Using environment variable for download auth.")
        auth = os.getenv("DOWNLOAD_AUTH")
    try:
        res = requests.post(download.link, headers={"Authorization": auth})
        if res.status_code != 200:
            logger.info(f"Failed to download torrent info for {download.title} - {download.uid}: HTTP {res.status_code}")
            return False
    except requests.exceptions.RequestException:
        logger.exception(f"Network error while downloading torrent info for {download.title} - {download.uid}")
        return False
    dat = res.json()
    url1 = dat["url"]
    try:
        res2 = requests.get(url1)
        if res2.status_code != 200:
            logger.info(f"Failed to download torrent file for {download.title} - {download.uid}: HTTP {res2.status_code}")
            return False
    except requests.exceptions.RequestException:
        logger.exception(f"Network error while downloading torrent file for {download.title} - {download.uid}")
        return False
    start_download(file_content=res2.content, title=download.title, uid=download.uid, dirname=download.dirname,source=download.source, dbsession=dbsession)
    return True

Download_info = tuple[str,Literal["two_step","direct"],Literal["zip"]]

def force_download_info(source: str) -> Download_info | None:
    if re.match("https://nhentai.net/g/\\d+",source):
        idx = re.match("https://nhentai.net/g/(\\d+)",source).group(1)
        return f"https://nhentai.net/api/v2/galleries/{idx}/download?format=zip", "two_step", "zip"
    return None

def download_file(link: str, method: Literal["two_step","direct"]) -> bytes | None:
    headers = {}
    if os.getenv("DOWNLOAD_AUTH"):
        headers["Authorization"] = os.getenv("DOWNLOAD_AUTH")
    if method == "direct":
        try:
            res = requests.get(link,headers=headers)
            if res.status_code != 200:
                logger.info(f"Failed to download file from {link}: HTTP {res.status_code}")
                return None
            return res.content
        except Exception as e:
            logger.exception(f"Error downloading file from {link}: {e}")
            return None
    elif method == "two_step":
        try:
            res = requests.post(link,headers=headers)
            if res.status_code != 200:
                logger.info(f"Failed to download file info from {link}: HTTP {res.status_code}")
                return None
        except Exception as e:
            logger.exception(f"Error downloading file info from {link}: {e}")
            return None
        try:
            dat = res.json()
            url1 = dat["url"]
            res2 = requests.get(url1,headers=headers)
            if res2.status_code != 200:
                logger.info(f"Failed to download file info from {url1}: HTTP {res2.status_code}")
                return None
            return res2.content
        except Exception as e:
            logger.exception(f"Error downloading file from {link}: {e}")
            return None
    return None

def save_to(content: bytes, file_format: Literal["zip"], target: str) -> bool:
    if file_format == "zip":
        with io.BytesIO(content) as buffer:
            with ZipFile(buffer) as zip_file:
                os.makedirs(target, exist_ok=True)
                zip_file.extractall(target)
        return True
    else:
        logger.error(f"Unsupported file format {file_format} for saving to {target}")
        return False

def force_download(book: datas.Book, dbsession) -> bool:
    info = force_download_info(book.source)
    if info is None:
        return False
    link, method, file_format = info
    logger.info(f"Trying to force download {book.title} - {book.uid} from {link} using method {method}")
    file_content = download_file(link, method)
    if file_content is None:
        return False
    logger.info(f"Successfully downloaded file for {book.title} - {book.uid} from {link}. Saving to disk.")
    if not save_to(file_content, file_format, str(constants.inner_book_path / book.dirname / "TMP_DIR")):
        return False
    resolve(dbsession, book.uid)
    return False

"""
Value	Description
error	Some error occurred, applies to paused torrents
missingFiles	Torrent data files is missing
uploading	Torrent is being seeded and data is being transferred
pausedUP	Torrent is paused and has finished downloading
queuedUP	Queuing is enabled and torrent is queued for upload
stalledUP	Torrent is being seeded, but no connection were made
checkingUP	Torrent has finished downloading and is being checked
forcedUP	Torrent is forced to uploading and ignore queue limit
allocating	Torrent is allocating disk space for download
downloading	Torrent is being downloaded and data is being transferred
metaDL	Torrent has just started downloading and is fetching metadata
pausedDL	Torrent is paused and has NOT finished downloading
queuedDL	Queuing is enabled and torrent is queued for download
stalledDL	Torrent is being downloaded, but no connection were made
checkingDL	Same as checkingUP, but torrent has NOT finished downloading
forcedDL	Torrent is forced to downloading to ignore queue limit
checkingResumeData	Checking resume data on qBt startup
moving	Torrent is moving to another location
unknown	Unknown status
"""


stalled_cnt: dict[str, int] = defaultdict(int)
total_stalled_cnt: dict[str, int] = defaultdict(int)
BREAK_THRESHOLD = 15
FORCE_THRESHOLD = 300
FAILED_DECREASE = 20


def scan_torrents(dbsession: Session):
    uids = []
    cnt = 0
    has_queued = False
    rms = []
    for book in dbsession.query(datas.Book).filter_by(completed=False).all():
        h = book.torrent_hash
        cnt += 1
        try:
            torrents = qbt_client.torrents_info(hashes=h)
            if not torrents:
                logger.warning(f"No torrent found for {book.title} - {book.uid} with hash {h}. Marking as removed.")
                rms.append(book.uid)
                continue
            torrent = torrents[0]
            if torrent.state_enum.is_uploading:
                torrent.delete()
                uids.append(book.uid)
                if h in total_stalled_cnt:
                    del total_stalled_cnt[h]
            elif torrent.state_enum is TorrentState.QUEUED_DOWNLOAD:
                has_queued = True
            if torrent.state_enum is TorrentState.STALLED_DOWNLOAD:
                stalled_cnt[h] += 1
                total_stalled_cnt[h] += 1
            elif h in stalled_cnt:
                del stalled_cnt[h]
        except Exception as e:
            logger.exception(f"Error checking torrent status for {book.title} - {book.uid}: {e}")
    if not uids:
        if has_queued and max(stalled_cnt.values()) >= BREAK_THRESHOLD:
            t = max(stalled_cnt.items(), key=lambda x: x[1])
            logger.warning(f"Detected stalled torrents with hash {t[0]} for {t[1]} consecutive checks. Move it to the bottom of queue")
            try:
                qbt_client.torrents_bottom_priority(torrent_hashes=t[0])
            except Exception as e:
                logger.exception(f"Error moving stalled torrent with hash {t[0]} to bottom of queue: {e}")
            stalled_cnt.clear()
        elif max(total_stalled_cnt.values()) >= FORCE_THRESHOLD:
            t = max(total_stalled_cnt.items(), key=lambda x: x[1])
            logger.info(f"Detected stalled torrents with hash {t[0]} for {t[1]} consecutive checks. Try force download.")
            try:
                res = force_download(dbsession.query(datas.Book).filter_by(torrent_hash=t[0]).first(), dbsession)
                if res:
                    logger.info(f"Force download succeeded for torrent with hash {t[0]}.")
                    del total_stalled_cnt[t[0]]
                else:
                    logger.warning(f"Force download failed for torrent with hash {t[0]}. Will try again later.")
                    total_stalled_cnt[t[0]] -= FAILED_DECREASE
            except Exception as e:
                logger.exception(f"Error force downloading torrent with hash {t[0]}: {e}")
                total_stalled_cnt[t[0]] -= FAILED_DECREASE
    for uid in uids:
        cnt -= 1
        resolve(dbsession, uid)
    for uid in rms:
        cnt -= 1
        dbsession.delete(dbsession.query(datas.Book).filter_by(uid=uid).first())
    if uids:
        if cnt > 0:
            logger.info(f"{cnt} downloads remaining.")
        else:
            logger.info("All downloads completed.")


def scan_downloads(dbsession: Session):
    nxt = math.floor(time.time() + 60)
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

def background_worker():
    with server.app.app_context():
        while True:
            try:
                with datas.SessionContext() as dbsession:
                    scan_torrents(dbsession)
            except Exception as e:
                logger.exception(f"Error scanning torrents: {e}")
            try:
                with datas.SessionContext() as dbsession:
                    scan_downloads(dbsession)
            except Exception as e:
                logger.exception(f"Error scanning downloads: {e}")
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
                logger.exception(f"Error deleting old torrent for {old.title} - {uid}: {e}")
        session.delete(old)
        session.flush()
    hash_val = calculate_torrent_hash(file_content)
    res = qbt_client.torrents_add(torrent_files=file_content, save_path=str(constants.inner_book_path / dirname))
    if res != "Ok.":
        logger.exception(f"Failed to add torrent for {title} - {uid}: {res}")
        return
    if not title:
        try:
            title = extract_torrent_title(file_content)
        except Exception as e:
            logger.exception(f"Failed to extract title from torrent for {uid}: {e}")
            return
    if not hash_val:
        logger.exception(f"Failed to retrieve torrent hash for {title} - {uid}")
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
                logger.exception(f"Error deleting old torrent for {old.title} - {uid}: {e}")
        datas.db.session.delete(old)
        datas.db.session.flush()
    logger.debug(f"Prepared download for {title} - {uid}, source: {source}")
    if title is None:
        title = ""
    dat = datas.Download(uid=uid, title=title, dirname=dirname, source=source, auth=auth, link=link,
                         wait=math.floor(time.time()-10))
    datas.db.session.add(dat)
    datas.db.session.commit()