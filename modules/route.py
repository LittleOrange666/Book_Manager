from flask import render_template, request
from flask_login import login_required
from flask_restx import abort

from . import server, constants

app = server.app


@login_required
@app.route('/icon/<dirname>')
def icon(dirname):
    from flask import send_file
    path = constants.book_path / dirname / 'icon.ico'
    if path.exists():
        return send_file(path, mimetype='image/x-icon')
    else:
        return "", 404


@login_required
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
@login_required
def book_page(uid):
    return render_template('book.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/signup')
def signup_page():
    if request.headers.get('X-Forwarded-For') is not None:
        abort(403, "Signup is disabled behind proxy")
    return render_template('signup.html')


def init():
    pass
