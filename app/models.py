from . import db, 
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login

class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(64), index = True, unique = True)
  email = db.Column(db.String(120), index = True, unique = True)
  passwordHash = db.Column(db.String(128))
  failedAttempts = db.Column(db.Integer, default=0)
  lockedUntil = db.Column(db.DateTime, nullable=True)
  mfaEnabled = db.Column(db.Boolean, default=False)
  lastLoginAt = db.Column(db.DateTime, nullable=True)
  lastLoginIP = db.Column(db.String(45), nullable=True)

  def setPassword(self, password):
    self.password_hash = generate_password_hash(password)

  def checkPassword(self, password):
    return check_password_hash(self.passwordHash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
