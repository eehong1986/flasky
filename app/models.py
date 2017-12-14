#-*- coding:utf-8 -*-

import bleach
from markdown import markdown
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, url_for
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db
from . import login_manager

class Permission(object):
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80

# 建立数据库使用的模型
class Role(db.Model):
    __tablename__ = 'roles'
    # role id
    id = db.Column(db.Integer, primary_key=True)
    # role name
    name = db.Column(db.String(64), unique=True)
    # default role or not
    default = db.Column(db.Boolean, default=False, index=True)
    # permissions of role
    permissions = db.Column(db.Integer)
    # 建立联系 users代表这个关系的面向对象视角
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def insert_roles():
        roles = {
            'User' : (Permission.FOLLOW 
                    | Permission.COMMENT 
                    | Permission.WRITE_ARTICLES, True),
            'Moderator' : (Permission.FOLLOW
                         | Permission.COMMENT
                         | Permission.WRITE_ARTICLES
                         | Permission.MODERATE_COMMENTS, False),
            'Administer' : (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body_html = db.Column(db.Text)

    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    # 把文章转换成JSON格式的序列化字典
    def to_json(self):
        json_post = {
                'url' : url_for('api.get_post', id=self.id, _external=True),
                'body' : self.body,
                'body_html' : self.body_html,
                'timestamp' : self.timestamp,
                'author' : url_for('api.get_user', id=self.author_id, _external=True),
                'comments' : url_for('api.get_post_comments', id=self.id, _external=True),
                'comment_count' : self.comments.count()
            }
        return json_post

    # 从JSON格式数据创建一篇博客文章
    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            return ValidationError('post does not have a body')
        return Post(body=body)
    
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count=User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            post = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                        timestamp=forgery_py.date.date(True),
                        author=u)
            db.session.add(post)
            db.session.commit()
    
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronnym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

db.event.listen(Post.body, 'set', Post.on_changed_body)

class Comment(db.Model):
    __tablename__= 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    def to_json(self):
        json_comment = {
            'url' : url_for('api.get_comment', id=self.id, _external=True),
            'body' : self.body,
            'body_html' : self.body_html,
            'author' : url_for('api.get_user', \
                        id=self.author_id, _external=True),
            'post' : url_for('api.get_post', id=self.post_id, _external=True)
        }
        return json_comment
    
    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            return ValidationError('Comment does not have a body')
        return Comment(body=body)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronnym', 'b','code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

db.event.listen(Comment.body, 'set', Comment.on_changed_body)

# 记录用户关注与被关注信息的关联表
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"), 
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey("users.id"), 
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    # user id
    id = db.Column(db.Integer, primary_key=True)
    # user email address
    email = db.Column(db.String(64), unique=True, index=True)
    # user name
    username = db.Column(db.String(32), unique=True, index=True)
    # user password
    password_hash = db.Column(db.String(128))
    # user comfirmed by email or not
    confirmed = db.Column(db.Boolean, default=False)
    # 用户姓名
    name = db.Column(db.String(64))
    # 用户居住地
    location = db.Column(db.String(64))
    # 简介
    about_me = db.Column(db.Text())
    # 注册时间
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    # 最后一次访问时间
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    # 此处添加的role_id被定义为外键，就是这个外键建立起了到Role的联系
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    # 定义用户的关注者以及被关注者的多对多关系
    followed = db.relationship('Follow', 
                                foreign_keys=[Follow.follower_id],
                                backref=db.backref('follower', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # 如果基类对象创建后没有定义角色，根据电子邮件地址决定用户角色
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            else:
                self.role = Role.query.filter_by(default=True).first()
        # 创建新用户时自动关注自己
        self.follow(self)

    def __repr__(self):
        return '<User %r>' % self.username

    def can(self, permissions):
        return self.role is not None and \
                (self.role.permissions & permissions)

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    # 用户访问页面时更新last_seen
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm' : self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset' : self.id})

    def reset_password(self, token, password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = password
        db.session.add(self)
        return True
   
    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email' : self.id, 'new_email' : new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if User.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    # 生成http验证使用的签名令牌
    def generate_auth_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], 
                        expires_in=expiration)
        return s.dumps({'id' : self.id })

    # 把用户转换成JSON格式的序列化字典
    def to_json(self):
        json_user = {
                'url' : url_for('api.get_user', id=self.id, _external=True),
                'user_name' : self.username,
                'member_since' : self.member_since,
                'last_seen' : self.last_seen,
                'posts' : url_for('api.get_user_posts', id=self.id, _external=True),
                'followed_posts' : url_for('api.get_user_timeline', \
                                        id=self.id, _external=True),
                'post_count' : self.posts.count()
            }
        return json_user

    # 如果令牌可用，返回对应的用户
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])


    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
                .filter(Follow.follower_id == self.id)
    
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower = self, followed = user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(
                followed_id=user.id).first() is not None

    def if_followed_by(self, user):
        return self.followers.filter_by(
                follower_id=user.id).first() is not None

    # 为数据库中已有用户添加自关注信息
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                    username=forgery_py.internet.user_name(True),
                    password=forgery_py.lorem_ipsum.word(),
                    confirmed=True,
                    name=forgery_py.name.full_name(),
                    location=forgery_py.lorem_ipsum.sentence(),
                    member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class AnonymousUser(AnonymousUserMixin):
    
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager.anonymous_user = AnonymousUser

