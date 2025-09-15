import os
import shutil
import threading

from gunicorn.app.base import BaseApplication

from modules import server, datas, constants, route, api, downloader

app = server.app


class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config_data = {key: value for key, value in self.options.items()
                       if key in self.cfg.settings and value is not None}
        for key, value in config_data.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    if not downloader.init():
        print("Failed to initialize downloader module.")
        return
    with app.app_context():
        datas.db.create_all()
        bads = datas.Book.query.filter_by(completed=False).all()
        for bad in bads:
            path = constants.book_path / bad.dirname
            if path.exists() and path.is_dir():
                shutil.rmtree(path)
            datas.db.session.delete(bad)
        datas.db.session.commit()
    threading.Thread(target=downloader.background_worker, daemon=True).start()
    port = os.environ.get('SERVER_PORT', '5000')
    options = {
        'bind': '%s:%s' % ('[::]', str(port)),
        'workers': 4,
        'timeout': 120,
    }
    StandaloneApplication(app, options).run()


if __name__ == '__main__':
    main()
