import base64
import io
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
import pyotp
import qrcode
from app.models import User
from urllib.parse import urlparse
from flask_login import current_user, login_user, logout_user, login_required
from app import db, limiter
from forms import LoginForm, LogoutForm
from datetime import datetime, timedelta, timezone
import logging
import json


main = Blueprint('main', __name__)

def get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)

@limiter.limit("7 per minute")
@main.route('/login', methods=['GET', 'POST']) 
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    show_captcha = False
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.locked_until:
            now = datetime.now(timezone.utc)
            if user.locked_until > now:
                time_remaining = user.locked_until - now
                minutes = int(time_remaining.total_seconds() / 60) 
                seconds = int(time_remaining.total_seconds() % 60) 
                flash(f'Account Is Locked. Please Try Again In {minutes} Minutes And {seconds} Seconds.', 'danger')
                return redirect(url_for('main.login'))
            else:
                user.locked_until = None
                db.session.commit()
        
        if user and user.failed_attempts >= 3 and user.failed_attempts < 5:
            show_captcha = True
            if not show_captcha:  
                logging.info(json.dumps({
                    "event": "captcha_trigger",
                    "username": user.username,
                    "client_ip": get_client_ip(),
                    "failed_attempts": user.failed_attempts
                }))
            if form.recaptcha.errors:
                flash('Please Complete The CAPTCHA Verification Correctly.', 'warning')
                return render_template('login.html', title='Sign In', form=form, show_captcha=show_captcha)
        
        if user is None or not user.check_password(form.password.data):
            logging.warning(json.dumps({
                "event": "password_failure",
                "username": form.username.data,
                "client_ip": get_client_ip(),
                "user_exists": user is not None
            }))
            
            if user:
                user.failed_attempts += 1
                
                if user.failed_attempts >= 5:
                    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=5)
                    user.failed_attempts = 0
                    logging.warning(json.dumps({
                        "event": "account_lockout",
                        "username": user.username,
                        "client_ip": get_client_ip(),
                        "reason": "excessive_failed_attempts"
                    }))
                    flash('Too Many Failed Login Attempts. Account Locked For 5 Minutes.', 'danger')
                    db.session.commit()
                    return redirect(url_for('main.login'))
                
                db.session.commit()
            
            flash('Invalid Username or Password', 'danger')
            return redirect(url_for('main.login'))
        
        user.failed_attempts = 0
        user.locked_until = None
        db.session.commit()
        
        if user.mfa_enabled:
            session['pending_mfa_user_id'] = user.id
            return redirect(url_for('main.mfa_verify'))
        elif not user.mfa_secret:
            session['pending_mfa_user_id'] = user.id
            return redirect(url_for('main.mfa_setup'))
        
        session.clear()  
        login_user(user, remember=False, fresh=True)
        logging.info(json.dumps({
            "event": "login_success",
            "username": user.username,
            "client_ip": get_client_ip(),
            "mfa_enabled": False
        }))
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        return redirect(next_page)
    
    if request.method == 'GET' and form.username.data:
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.failed_attempts >= 3:
            show_captcha = True
    
    return render_template('login.html', title='Sign In', form=form, show_captcha=show_captcha)

@main.route('/mfa/setup', methods=['GET', 'POST'])
def mfa_setup():
    from forms import MFAVerifyForm
    import qrcode
    from io import BytesIO
    import base64
    
    user_id = session.get('pending_mfa_user_id')
    if not user_id:
        flash('Please Login First.', 'warning')
        return redirect(url_for('main.login'))
    
    user = User.query.get(user_id)
    if not user:
        session.pop('pending_mfa_user_id', None)
        return redirect(url_for('main.login'))
    
    if not user.mfa_secret:
        user.mfa_secret = pyotp.random_base32()
        db.session.commit()
    
    form = MFAVerifyForm()
    
    if form.validate_on_submit():
        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(form.totp_code.data, valid_window=1):
            user.mfa_enabled = True
            db.session.commit()
            
            session.pop('pending_mfa_user_id', None)
            session.clear()
            login_user(user, remember=False, fresh=True)
            
            logging.info(json.dumps({
                "event": "mfa_setup_success",
                "username": user.username,
                "client_ip": get_client_ip()
            }))
            flash('MFA Has Been Successfully Enabled!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            logging.warning(json.dumps({
                "event": "invalid_totp",
                "context": "mfa_setup",
                "username": user.username,
                "client_ip": get_client_ip()
            }))
            flash('Invalid Code. Please Try Again.', 'danger')
    
    totp_uri = pyotp.totp.TOTP(user.mfa_secret).provisioning_uri(
        name=user.username,
        issuer_name="CSC2031 App"
    )
    
    qr = qrcode.make(totp_uri)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('mfa_setup.html', 
                         form=form,
                         qr_code=qr_b64,
                         secret=user.mfa_secret)


@main.route('/mfa/verify', methods=['GET', 'POST'])
def mfa_verify():
    from forms import MFAVerifyForm
    
    user_id = session.get('pending_mfa_user_id')
    if not user_id:
        flash('Please Login First.', 'warning')
        return redirect(url_for('main.login'))
    
    user = User.query.get(user_id)
    if not user or not user.mfa_enabled:
        session.pop('pending_mfa_user_id', None)
        return redirect(url_for('main.login'))
    
    form = MFAVerifyForm()
    
    if form.validate_on_submit():
        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(form.totp_code.data, valid_window=1):
            session.pop('pending_mfa_user_id', None)
            session.clear()
            login_user(user, remember=False, fresh=True)
            
            logging.info(json.dumps({
                "event": "login_success",
                "username": user.username,
                "client_ip": get_client_ip(),
                "mfa_enabled": True
            }))
            flash('Login Successful!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            logging.warning(json.dumps({
                "event": "invalid_totp",
                "context": "mfa_verify",
                "username": user.username,
                "client_ip": get_client_ip()
            }))
            flash('Invalid Authentication Code. Please Try Again.', 'danger')
    
    return render_template('mfa_verify.html', form=form, username=user.username)

@main.route('/dashboard')
@login_required
def dashboard():
    logout_form = LogoutForm()
    return render_template('dashboard.html', logout_form=logout_form)

@main.route('/logout', methods=['POST'])
@login_required
def logout():
    logging.info(json.dumps({
        "event": "logout",
        "username": current_user.username,
        "client_ip": get_client_ip()
    }))
    logout_user()
    session.clear()
    flash('You Have Been Logged Out.', 'info')
    return redirect(url_for('main.login'))

