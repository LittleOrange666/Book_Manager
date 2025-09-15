from flask import Flask
from flask_cors import CORS

app = Flask(__name__, static_url_path='', static_folder='../static', template_folder='../templates')

CORS(app, resources={r"/api/*": {"origins": "*"}})
