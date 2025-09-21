import hashlib
import os
import shutil
import time

import bencodepy
import qbittorrentapi
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


def background_worker():
    with server.app.app_context():
        while True:
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


def start_download(file_content: bytes, title: str, uid: str, dirname: str, source: str):
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
    datas.db.session.add(dat)
    datas.db.session.commit()
