import os
from contextlib import contextmanager

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker

from . import server, constants

app = server.app
datafile = constants.data_path / "data.sqlite"
sqlite_url = 'sqlite:///' + str(datafile)
if all(k in os.environ for k in ("MYSQL_DB", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_HOST")):
    DB = os.environ["MYSQL_DB"]
    USER = os.environ["MYSQL_USER"]
    PASSWORD = os.environ["MYSQL_PASSWORD"]
    HOST = os.environ["MYSQL_HOST"]
    mysql_url = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DB}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = mysql_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True
    }
elif all(k in os.environ for k in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST")):
    DB = os.environ["POSTGRES_DB"]
    USER = os.environ["POSTGRES_USER"]
    PASSWORD = os.environ["POSTGRES_PASSWORD"]
    HOST = os.environ["POSTGRES_HOST"]
    postgres_url = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}/{DB}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = postgres_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True
    }
else:
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_url

db = SQLAlchemy(app)


class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    dirname = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=True)
    source = db.Column(db.String(100), nullable=True)
    torrent_hash = db.Column(db.String(40), nullable=True)


@contextmanager
def SessionContext():
    session = sessionmaker(bind=db.engine)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
