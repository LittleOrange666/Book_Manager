import uuid

from flask_restx import Api, Resource, reqparse, fields
from werkzeug.datastructures import FileStorage

from . import server, downloader, constants, datas

app = server.app

api = Api(app, title="Book Manager API", description="API for Book Manager", doc="/api-docs", prefix="/api")

book_post_input = reqparse.RequestParser()
book_post_input.add_argument('title', type=str, required=True, help='Title of the book')
book_post_input.add_argument('uid', type=str, required=True, help='Unique identifier of the book')
book_post_input.add_argument('source', type=str, required=False, help='Source of the book')
book_post_input.add_argument('file', type=FileStorage, location='files', required=True, help='File content of the book')
book_post_input.add_argument('admin_key', type=str, required=False, help='Admin key for authentication')

book_post_output = api.model('BookCreationResponse', {
    'message': fields.String(description="Response message")
})

book_put_input = reqparse.RequestParser()
book_put_input.add_argument('title', type=str, required=True, help='Title of the book')
book_put_input.add_argument('uid', type=str, required=True, help='Unique identifier of the book')
book_put_input.add_argument('source', type=str, required=False, help='Source of the book')
book_put_input.add_argument('dirname', type=str, required=True, help='dirname of the book')
book_put_input.add_argument('admin_key', type=str, required=False, help='Admin key for authentication')

book_put_output = api.model('BookCreationResponse', {
    'message': fields.String(description="Response message")
})

book_get_input = reqparse.RequestParser()
book_get_input.add_argument('uid', type=str, required=True, help='Unique identifier of the book')

book_get_output = api.model('BookStatus', {
    'title': fields.String(description="Book title"),
    'source': fields.String(description="Book source"),
    'dirname': fields.String(description="Book dirname"),
    'files': fields.List(fields.String, description="List of image files")
})

index_get_input = reqparse.RequestParser()
index_get_input.add_argument('begin', type=int, required=False, default=1, help='Begin book order')
index_get_input.add_argument('count', type=int, required=False, default=10, help='Number of items')

index_get_output = api.model('BookIndex', {
    'books': fields.List(fields.Nested(api.model('BookItem', {
        'title': fields.String(description="Book title"),
        'uid': fields.String(description="Unique identifier of the book"),
        'dirname': fields.String(description="Directory name of the book")
    })), description="List of books"),
    "length": fields.Integer(description="Number of books returned")
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
            title=args['title'],
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


@api.route("/index")
class Index(Resource):
    @api.doc("get_index")
    @api.expect(index_get_input)
    @api.marshal_with(index_get_output)
    def get(self):
        args = index_get_input.parse_args()
        begin = args.get('begin', 1)
        count = args.get('count', 10)
        if begin < 1 or count < 1 or count > 100:
            return {"message": "Invalid parameters"}, 400
        books = datas.Book.query.filter_by(completed=True).order_by(datas.Book.id.desc()).offset(begin - 1).limit(count).all()
        result = []
        for book in books:
            result.append({
                "title": book.title,
                "uid": book.uid,
                "dirname": book.dirname
            })
        return {"books": result, "length": len(result)}, 200


def init():
    pass
