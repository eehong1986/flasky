#-*- coding:utf-8 -*-

from flask import jsonify, request, current_app, url_for, g
from . import api
from .authentication import auth
from .decorators import permission_required
from ..models import Post, Comment, Permission
from .. import db

# post资源相关端点

# 创建新博客文章
@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post():
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()), 201, \
            {'Location': url_for('api.get_post', id=post.id, _external=True)}

# 请求站点博客集合
@api.route('/posts/')
@auth.login_required
def get_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)

    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', page=page+1, _external=True)

    return jsonify({'posts' : [post.to_json() for post in posts],
                    'prev' : prev,
                    'next' : next,
                    'count': pagination.total})

# 请求指定id 的某篇博客
@api.route('/posts/<int:id>')
@auth.login_required
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())

# 更新现有博客文章
@api.route('/posts/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(id):
    post = Post.query.get_or_404(id)
    if g.current_user != post.author and \
            not g.current_user.can(Permission.ADMINISTER):
        return forbidden('Insufficient permissions')
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    return jsonify(post.to_json())

# 获取一篇博客文章中的所有评论
@api.route('/posts/<int:id>/comments/')
@auth.login_required
def get_post_comments(id):
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = post.comments.paginate(
            page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
            error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_post_comments', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_post_comments', page=page+1, _external=True)
    return jsonify({'comments' : \
                            [comment.to_json() for comment in comments],
                    'prev' : prev,
                    'next' : next,
                    'count': pagination.total})


# 向某篇博客文章中添加评论
@api.route('/posts/<int:id>/comments/', methods=['POST'])
@permission_required(Permission.COMMENT)
def new_comment(id):
    post = Post.query.get_or_404(id)
    comment = Comment.from_json(request.json)
    comment.author = g.current_user
    comment.post = post
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_json()), 201, \
            {'Location': url_for('api.get_post_comments', id=post.id, _external=True)}
