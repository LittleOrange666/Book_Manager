import os
from pathlib import Path

base_path = Path(os.path.dirname(os.path.dirname(__file__))).absolute()
book_path = base_path / os.environ.get("BOOK_PATH", "./books")
data_path = base_path / os.environ.get("DATA_PATH", "./data")
inner_book_path = Path("/downloads")
exts = ("jpg", "jpeg", "png", "gif", "icns", "ico", "webp")
