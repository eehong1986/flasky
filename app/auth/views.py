#-*- coding:utf-8 -*-

from flask import render_template, session, redirect, url_for, flash, request
from flask_login import login_required, login_user, logout_user, current_user
#from flask import before_request

from . import auth
from ..models import User, Role
from .. import db
from ..email import send_email
from .forms import LoginForm,RegistrationForm

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        role_user = Role.query.filter_by(name='User').first()
        user = User(email = form.email.data,
                username = form.username.data,
                password = form.password.data)
        db.session.add(user)
        # ** 这里必须先提交数据库操作之后，数据库才能为新用户赋予id值
        db.session.commit()
        # 生成验证令牌并给新用户发送确认email
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account',
                'auth/email/confirm', user=user, token=token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    # 如果用户已确认过，直接返回主页
    if current_user.confirmed:
        return redirect('url_for(main.index)')
    # 处理用户确认token
    if current_user.confirm(token):
        # 在confirm()方法中处理数据库的更新操作，此处无须再处理
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))

@auth.route('/confirm')
@login_required
def resend_confirmation():
    # 生成验证令牌并给用户重新发送确认email
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
            'auth/email/confirm', user=current_user, token=token)
    flash('A confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))

# 过滤未确认账户的用户
@auth.before_app_request
def before_request():
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint \
            and request.endpoint[:5] != 'auth.' \
            and request.endpoint != 'static':
                return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/secret')
@login_required
def secret():
    return 'Only authenticated users are allowed!'

