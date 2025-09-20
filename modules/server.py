import os
import secrets
from datetime import timedelta

import redis
from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__, static_url_path='', static_folder='../static', template_folder='../templates')

CORS(app, resources={r"/api/*": {"origins": "*"}})

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

redis_host = os.environ.get("REDIS_HOST", "localhost")

app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", secrets.token_urlsafe(33))

app.config['SESSION_TYPE'] = "redis"
app.config["SESSION_COOKIE_NAME"] = "BookManagerSession"
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.StrictRedis(host=redis_host)
app.config['SESSION_KEY_PREFIX'] = 'session:'
app.config['SESSION_PERMANENT'] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
