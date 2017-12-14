#-*- coding:utf-8 -*-

# ���ļ�ʵ�� comment ��Դ�йصĶ˵�

from flask import jsonify, request, current_app, url_for
from . import api
from .authentication import auth
from ..models import Comment

# ��ȡƽ̨����������Դ
@api.route('/comments/')
@auth.login_required
def get_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.paginate(
            page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
            error_out=True)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_comments', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_comments', page=page+1, _external=True)
    return jsonify({'comments' : [comment.to_json() for comment in comments],
                    'prev': prev,
                    'next': next,
                    'count': pagination.total})

# ��ȡָ����ĳƪ������Դ
@api.route('/comments/<int:id>')
@auth.login_required
def get_comment(id):
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())
