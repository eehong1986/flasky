#-*- coding:utf-8 -*-

from . import db

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
