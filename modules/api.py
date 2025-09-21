import shutil
import uuid
from functools import wraps

from flask import request
from flask_login import login_user, login_required, logout_user, current_user
from flask_restx import Api, Resource, reqparse, fields, abort
from werkzeug.datastructures import FileStorage

from . import server, downloader, constants, datas, login

app = server.app

api = Api(app, title="Book Manager API", description="API for Book Manager", doc="/api-docs", prefix="/api")


def login_required_api(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401, "Unauthorized")
        return f(*args, **kwargs)

    return decorated


book_post_input = reqparse.RequestParser()
book_post_input.add_argument('title', type=str, required=False, help='Title of the book', location='form')
book_post_input.add_argument('uid', type=str, required=True, help='Unique identifier of the book', location='form')
book_post_input.add_argument('source', type=str, required=False, help='Source of the book', location='form')
book_post_input.add_argument('file', type=FileStorage, location='files', required=True, help='File content of the book')
book_post_input.add_argument('admin_key', type=str, required=False, help='Admin key for authentication',
                             location='form')

book_post_output = api.model('BookCreationResponse', {
    'message': fields.String(description="Response message")
})

book_put_input = reqparse.RequestParser()
book_put_input.add_argument('title', type=str, required=True, help='Title of the book', location='form')
book_put_input.add_argument('uid', type=str, required=True, help='Unique identifier of the book', location='form')
book_put_input.add_argument('source', type=str, required=False, help='Source of the book', location='form')
book_put_input.add_argument('dirname', type=str, required=True, help='dirname of the book', location='form')
book_put_input.add_argument('admin_key', type=str, required=False, help='Admin key for authentication', location='form')

book_put_output = api.model('BookMigrateResponse', {
    'message': fields.String(description="Response message")
})

book_get_input = reqparse.RequestParser()
book_get_input.add_argument('uid', type=str, required=True, help='Unique identifier of the book', location='args')

book_get_output = api.model('BookStatus', {
    'title': fields.String(description="Book title"),
    'source': fields.String(description="Book source"),
    'dirname': fields.String(description="Book dirname"),
    'files': fields.List(fields.String, description="List of image files")
})

book_delete_input = reqparse.RequestParser()
book_delete_input.add_argument('uid', type=str, required=True, help='Unique identifier of the book', location='form')
book_delete_input.add_argument('admin_key', type=str, required=False, help='Admin key for authentication',
                               location='form')

book_delete_output = api.model('BookRemoveResponse', {
    'message': fields.String(description="Response message")
})

index_get_input = reqparse.RequestParser()
index_get_input.add_argument('begin', type=int, required=False, default=1, help='Begin book order', location='args')
index_get_input.add_argument('count', type=int, required=False, default=10, help='Number of items', location='args')

index_get_output = api.model('BookIndex', {
    'books': fields.List(fields.Nested(api.model('BookItem', {
        'title': fields.String(description="Book title"),
        'uid': fields.String(description="Unique identifier of the book"),
        'dirname': fields.String(description="Directory name of the book"),
        'source': fields.String(description="Source of the book")
    })), description="List of books"),
    "length": fields.Integer(description="Number of books returned")
})

login_post_input = reqparse.RequestParser()
login_post_input.add_argument('username', type=str, required=True, help='Username', location='form')
login_post_input.add_argument('password', type=str, required=True, help='Password', location='form')

login_post_output = api.model('LoginResponse', {
    'message': fields.String(description="Response message")
})

logout_post_output = api.model('LogoutResponse', {
    'message': fields.String(description="Response message")
})

signup_post_input = reqparse.RequestParser()
signup_post_input.add_argument('username', type=str, required=True, help='Username', location='form')
signup_post_input.add_argument('password', type=str, required=True, help='Password', location='form')

signup_post_output = api.model('SignupResponse', {
    'message': fields.String(description="Response message")
})


@api.route("/book")
class BookIndex(Resource):
    @api.doc("create_book")
    @api.expect(book_post_input)
    @api.marshal_with(book_post_output)
    def post(self):
        args = book_post_input.parse_args()
        input_admin_key = args.get('admin_key', "")
        if constants.admin_key and input_admin_key != constants.admin_key:
            return {"message": "Invalid or missing admin key"}, 403
        dirname = args['uid'] + "_" + uuid.uuid4().hex
        downloader.start_download(
            file_content=args['file'].read(),
            title=args.get('title', ""),
            uid=args['uid'],
            dirname=dirname,
            source=args.get('source', "")
        )
        return {"message": "Book download started"}, 200

    @api.doc("migrate_book")
    @api.expect(book_put_input)
    @api.marshal_with(book_put_output)
    def put(self):
        args = book_put_input.parse_args()
        input_admin_key = args.get('admin_key', "")
        if constants.admin_key and input_admin_key != constants.admin_key:
            return {"message": "Invalid or missing admin key"}, 403
        title = args['title']
        uid = args['uid']
        source = args.get('source', "")
        dirname = args['dirname']
        path = constants.book_path / dirname
        if not path.exists() or not path.is_dir():
            return {"message": "Directory not found"}, 404
        old = datas.Book.query.filter_by(uid=uid).first()
        if old:
            return {"message": "Book with this UID already exists"}, 409
        dat = datas.Book(uid=uid, title=title, dirname=dirname, completed=True, source=source, torrent_hash="UNKNOWN")
        datas.db.session.add(dat)
        datas.db.session.commit()
        return {"message": "Book migrated successfully"}, 200

    @api.doc("get_book_status")
    @api.expect(book_get_input)
    @api.marshal_with(book_get_output)
    @login_required_api
    def get(self):
        args = book_get_input.parse_args()
        uid = args['uid']
        book = datas.Book.query.filter_by(uid=uid, completed=True).first()
        if not book:
            return {"message": "Book not found"}, 404
        path = constants.book_path / book.dirname
        fns = [f.name for f in path.iterdir() if f.suffix[1:].lower() in constants.exts]
        return {
            "title": book.title,
            "source": book.source,
            "dirname": book.dirname,
            "files": fns
        }, 200

    @api.doc("remove_book")
    @api.expect(book_delete_input)
    @api.marshal_with(book_delete_output)
    def delete(self):
        args = book_delete_input.parse_args()
        input_admin_key = args.get('admin_key', "")
        if constants.admin_key and input_admin_key != constants.admin_key:
            return {"message": "Invalid or missing admin key"}, 403
        uid = args['uid']
        book = datas.Book.query.filter_by(uid=uid, completed=True).first()
        if not book:
            return {"message": "Book not found"}, 404
        path = constants.book_path / book.dirname
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
        datas.db.session.delete(book)
        datas.db.session.commit()
        return {"message": "Book removed successfully"}, 200


@api.route("/index")
class Index(Resource):
    @api.doc("get_index")
    @api.expect(index_get_input)
    @api.marshal_with(index_get_output)
    @login_required_api
    def get(self):
        args = index_get_input.parse_args()
        begin = args.get('begin', 1)
        count = args.get('count', 10)
        if begin < 1 or count < 1 or count > 100:
            return {"message": "Invalid parameters"}, 400
        books = datas.Book.query.filter_by(completed=True).order_by(datas.Book.id.desc()).offset(begin - 1).limit(
            count).all()
        result = []
        for book in books:
            result.append({
                "title": book.title,
                "uid": book.uid,
                "dirname": book.dirname,
                "source": book.source
            })
        return {"books": result, "length": len(result)}, 200


@api.route("/login")
class Login(Resource):
    @api.doc("login")
    @api.expect(login_post_input)
    @api.marshal_with(login_post_output)
    def post(self):
        args = login_post_input.parse_args()
        username = args['username']
        password = args['password']
        user = login.try_login(username, password)
        if not user:
            return {"message": "Invalid username or password"}, 403
        login_user(user)
        return {"message": "Login successful"}, 200


@api.route("/signup")
class Signup(Resource):
    @api.doc("signup")
    @api.expect(signup_post_input)
    @api.marshal_with(signup_post_output)
    def post(self):
        if request.headers.get('X-Forwarded-For') is not None:
            return {"message": "Signup is disabled behind proxy"}, 403
        args = signup_post_input.parse_args()
        username = args['username']
        password = args['password']
        user = login.create_user(username, password)
        if not user:
            return {"message": "Signup Failed"}, 401
        login_user(user)
        return {"message": "Signup successful"}, 200


@api.route("/logout")
class Logout(Resource):
    @api.doc("logout")
    @api.marshal_with(logout_post_output)
    @login_required_api
    def post(self):
        logout_user()
        return {"message": "Logout successful"}, 200


def init():
    pass
