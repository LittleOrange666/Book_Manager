import asyncio
import shutil
import threading
import time
from pathlib import Path
from loguru import logger
import qbittorrentapi

from . import datas, constants

"""
session = lt.session()
_tasks = {}
_tasks_lock = threading.Lock()


def add_task(handle, uid):
    with _tasks_lock:
        _tasks[uid] = handle


def remove_task(uid):
    with _tasks_lock:
        if uid in _tasks:
            del _tasks[uid]


def resolve(dbsession, uid):
    info = dbsession.query(datas.Book).filter_by(uid=uid).first()
    info.completed = True
    path = constants.book_path / info.dirname
    if path.exists() and path.is_dir():
        files = [f for f in path.glob() if f.suffix[1:].lower() in constants.exts]
        files.sort(key=lambda x: x.stem)
        if files:
            info.icon_file = files[0].name
            logger.debug(f"Icon file of {info.title} - {uid} found: {info.icon_file}")
    logger.info(f"Complete downloading {info.title} - {uid}")
    dbsession.add(info)


def background_worker():
    while True:
        uids = []
        with _tasks_lock:
            for uid, handle in list(_tasks.items()):
                if handle.is_seed():
                    uids.append(uid)
        with _tasks_lock:
            for uid in uids:
                if uid in _tasks:
                    del _tasks[uid]
        with datas.SessionContext() as dbsession:
            for uid in uids:
                resolve(dbsession, uid)
        time.sleep(10)


def do_download(torrent_file, save_path, uid):
    torrent = TorrentDownloader(torrent_file, save_path)

    def on_complete():
        with datas.SessionContext() as dbsession:
            resolve(dbsession, uid)

    asyncio.run(torrent.start_download())


def start_download(file_content: bytes, title: str, uid: str, dirname: str, source: str):
    tmpfile = constants.data_path / "torrent" / f"{uid}.torrent"
    tmpfile.parent.mkdir(parents=True, exist_ok=True)
    with tmpfile.open("wb") as f:
        f.write(file_content)
    old = datas.Book.query.filter_by(uid=uid).first()
    if old:
        path = constants.book_path / old.dirname
        if path.exists() and path.is_dir():
            logger.info(f"Removing old one {old.title} - {uid}")
            shutil.rmtree(path)
        datas.db.session.delete(old)
        datas.db.session.flush()
    logger.info(f"Start downloading {title} - {uid}")
    params = {
        'save_path': str(constants.book_path / dirname),
    }
    info = lt.torrent_info(str(tmpfile))
    handle = session.add_torrent({'ti': info, **params})
    add_task(handle, uid)
    dat = datas.Book(uid=uid, title=title, dirname=dirname, completed=False, source=source)
    datas.db.session.add(dat)
    datas.db.session.commit()
"""

conn_info = {
    "host": "localhost",
    "port": 8082,
    "username": "admin",
    "password": "adminmeow"
}
qbt_client = qbittorrentapi.Client(**conn_info)


def init():
    try:
        qbt_client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        print(e)
        return False
    return True


def start_download(file_content: bytes, title: str, uid: str, dirname: str, source: str):
    qbt_client.torrents_add(torrent_files=file_content, save_path=str(constants.inner_book_path / dirname))
    dat = datas.Book(uid=uid, title=title, dirname=dirname, completed=False, source=source)
    datas.db.session.add(dat)
    datas.db.session.commit()
