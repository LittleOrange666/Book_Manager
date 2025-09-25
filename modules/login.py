from flask_login import LoginManager, UserMixin, current_user
from flask_restx import abort

from . import server, datas

app = server.app


class User(UserMixin):
    def __init__(self, _id, username, is_admin, info):
        self.inner_id = _id
        self.id = username
        self.username = username
        self.is_admin = is_admin
        self.info = info


def get_user(username):
    user_record = datas.User.query.filter_by(username=username).first()
    if user_record:
        return User(user_record.id, user_record.username, user_record.is_admin, user_record.info)
    return None


login_manager = LoginManager(app)
login_manager.session_protection = "basic"
login_manager.login_view = 'login_page'


@login_manager.user_loader
def user_loader(name):
    return get_user(name)


def try_login(username, password) -> User | None:
    user_record = datas.User.query.filter_by(username=username).first()
    if user_record and user_record.password == password:
        return User(user_record.id, user_record.username, user_record.is_admin, user_record.info)


def create_user(username, password, is_admin=False, info=""):
    if datas.User.query.filter_by(username=username).first():
        return None
    new_user = datas.User(username=username, password=password, is_admin=is_admin, info=info)
    datas.db.session.add(new_user)
    datas.db.session.commit()
    return get_user(username)


def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403, "Admin access required")


def init():
    pass
