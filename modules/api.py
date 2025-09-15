import uuid

from flask_restx import Api, Resource, reqparse
from werkzeug.datastructures import FileStorage

from . import server, downloader

app = server.app

api = Api(app, title="Book Manager API", description="API for Book Manager", doc="/api-docs", prefix="/api")

book_post_input = reqparse.RequestParser()
book_post_input.add_argument('title', type=str, required=True, help='Title of the book')
book_post_input.add_argument('uid', type=str, required=True, help='Unique identifier of the book')
book_post_input.add_argument('source', type=str, required=False, help='Source of the book')
book_post_input.add_argument('file', type=FileStorage, location='files', required=True, help='File content of the book')


@api.route("/book")
class BookIndex(Resource):
    @api.doc("create_book")
    @api.expect(book_post_input)
    def post(self):
        args = book_post_input.parse_args()
        dirname = args['uid'] + "_" + uuid.uuid5(uuid.NAMESPACE_DNS, args['title']).hex
        downloader.start_download(
            file_content=args['file'].read(),
            title=args['title'],
            uid=args['uid'],
            dirname=dirname,
            source=args.get('source', "")
        )
        return {"message": "Book download started", "uid": args['uid']}, 200
