#-*- coding:utf-8 -*-

from flask import Flask, render_template, session, redirect, url_for, flash
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_moment import Moment

# Flask 表单插件
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Required

# Flask 数据库ORM 插件
from flask_sqlalchemy import SQLAlchemy
# Flask 数据库迁移工具
from flask_migrate import Migrate, MigrateCommand

# Flask邮件支持
from flask_mail import Mail, Message

# 标准库
from datetime import datetime
import os
#import smtplib

app = Flask(__name__)
manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)

# 默认情况下，flask-wtf会保护表单免受跨站请求伪造攻击，需要为程序设置密钥
app.config['SECRET_KEY'] = 'HELLOSTRANGER'

# 配置smtp 服务器信息
app.config['MAIL_DEBUG'] = True
app.config['MAIL_SERVER'] = 'smtp.qq.com'       # smtp 服务器
app.config['MAIL_PORT'] = 465                   # smtp 服务器端口
app.config['MAIL_USE_SSL'] = True               # qq邮箱使用ssl
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') # 账号
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') # 密码

# 在实例化 Mail() 前必须配置smtp 服务器信息,
# 否则发送邮件建立socket时对象不知道服务器信息无法建立socket连接，返回10061错误
mail = Mail(app)

# 配置邮件header
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_MAIL_SENDER'] = 'Flasky Admin <346271437@qq.com>'
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN')

# Flask 数据库配置
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

# 建立数据库使用的模型
class Role(db.Model):
    __tablename__ = 'roles'
    # role id
    id = db.Column(db.Integer, primary_key=True)
    # role name
    name = db.Column(db.String(64), unique=True)
    # 建立联系 users代表这个关系的面向对象视角
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    # user id
    id = db.Column(db.Integer, primary_key=True)
    # user name
    username = db.Column(db.String(32), unique=True, index=True)
    # 此处添加的role_id被定义为外键，就是这个外键建立起了到Role的联系
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')

# 发送邮件
def send_mail(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject, 
            sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    mail.send(msg)


@app.route('/', methods=['GET', 'POST'])
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
            if app.config['FLASKY_ADMIN']:
                send_mail(app.config['FLASKY_ADMIN'], 'New User', 'mail/new_user', user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html', form=form, name=session.get('name'),
            known=session.get('known', False), current_time=datetime.utcnow())

@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    manager.run()
