# Imported Necessary Libraries
from app import db, login, bcrypt
from flask_login import UserMixin
from datetime import datetime

# Define User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    passwordHash = db.Column(db.String(128))
    failedAttempts = db.Column(db.Integer, default=0)
    lockedUntil = db.Column(db.DateTime, nullable=True)
    mfaEnabled = db.Column(db.Boolean, default=False)
    mfaSecret = db.Column(db.String(32), nullable=True)
    lastLoginAt = db.Column(db.DateTime, nullable=True)
    lastLoginIp = db.Column(db.String(45), nullable=True)

    # Password Hashing Methods (using bcrypt with 12 rounds for strong security) Copilot
    def setPassword(self, password):
        self.passwordHash = bcrypt.generate_password_hash(password).decode('utf-8')

    # Check Password Method
    def checkPassword(self, password):
        return bcrypt.check_password_hash(self.passwordHash, password)

# User Loader Callback
@login.user_loader
def loadUser(id):
    return User.query.get(int(id))
