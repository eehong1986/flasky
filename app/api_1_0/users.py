#-*- coding:utf-8 -*-

from flask import jsonify, request, current_app, url_for
from . import api
from .authentication import auth
from ..models import User

# 此文件实现 user 相关的资源端点

# 获取指定用户的信息
@api.route('/users/<int:id>')
@auth.login_required
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())

# 获取指定用户发布的博客文章
@api.route('/users/<int:id>/posts/')
@auth.login_required
def get_user_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.paginate(
            page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_post, page=page-1, _external=True')
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_post, page=page+1, _external=True')
    return jsonify({'user_posts' : [post.to_json() for post in posts],
                    'prev' : prev, 
                    'next' : next,
                    'count': pagination.total})

# 获取用户关注的用户发布的文章
@api.route('/users/<int:id>/timeline/')
@auth.login_required
def get_user_timeline(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_posts.paginate(
            page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out=False)
    followed_posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_timeline, page=page-1, _external=True')
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_timeline, page=page+1, _external=True')

    return jsonify({'followed_posts' : [post.to_json() \
                                        for post in followed_posts],
                    'prev' : prev,
                    'next' : next,
                    'count': pagination.total})


