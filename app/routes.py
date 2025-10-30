from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.models import User
from urllib.parse import urlparse
from flask_login import current_user, login_user, logout_user, login_required
from app import db, limiter
from forms import LoginForm


main = Blueprint('main', __name__)

@limiter.limit("7 per minute")
@main.route('/login', methods=['GET', 'POST']) 
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        session.clear()  
        login_user(user, remember=False, fresh=True)  
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@main.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

