#-*- coding:Utf-8 -*-

from datetime import datetime
from flask import render_template, session, redirect, url_for,current_app

from . import main
from .forms import NameForm
from ..email import send_email
from .. import db
from ..models import User, Role

@main.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            # 新用户，加入到数据库中
            role_user = Role.query.filter_by(name='User').first()
            user = User(username=form.name.data, role_id=role_user.id)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
            if current_app.config['FLASKY_ADMIN']:
                send_email(current_app.config['FLASKY_ADMIN'], 'New User', 'mail/new_user', user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('main.index'))
    return render_template('index.html', form=form, name=session.get('name'),
            known=session.get('known', False), current_time=datetime.utcnow())

@main.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)

