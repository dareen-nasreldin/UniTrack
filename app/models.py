from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, email, password_hash, created_at):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
