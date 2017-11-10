#-*- coding:utf-8 -*-

from . import db

# �������ݿ�ʹ�õ�ģ��
class Role(db.Model):
    __tablename__ = 'roles'
    # role id
    id = db.Column(db.Integer, primary_key=True)
    # role name
    name = db.Column(db.String(64), unique=True)
    # ������ϵ users���������ϵ����������ӽ�
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    # user id
    id = db.Column(db.Integer, primary_key=True)
    # user name
    username = db.Column(db.String(32), unique=True, index=True)
    # �˴���ӵ�role_id������Ϊ����������������������˵�Role����ϵ
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username
