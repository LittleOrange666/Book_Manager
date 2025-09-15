from flask import render_template

from . import server, constants

app = server.app


@app.route('/icon/<dirname>')
def icon(dirname):
    from flask import send_file
    path = constants.book_path / dirname / 'icon.ico'
    if path.exists():
        return send_file(path, mimetype='image/x-icon')
    else:
        return "", 404


@app.route('/image/<dirname>/<filename>')
def image(dirname, filename):
    from flask import send_file
    path = constants.book_path / dirname / filename
    if path.exists():
        return send_file(path)
    else:
        return "", 404


@app.route('/')
def index_page():
    return render_template('index.html')


@app.route('/books/<uid>')
def book_page(uid):
    return render_template('book.html')


def init():
    pass
