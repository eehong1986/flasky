#-*- coding:utf-8 -*-
from flask import jsonify
from . import api
from ..exceptions import ValidationError

# 自定义 400 错误响应
def bad_request(message):
    response = jsonify({'error' : 'bad request', 'message' : message})
    resposne.status_code = 400
    return response

# 自定义 401 错误响应
def unauthorized(message):
    response = jsonify({'error' : 'unauthorized', 'message' : message})
    response.status_code = 401
    return response

# 自定义 403 错误响应 
def forbidden(message):
    response = jsonify({'error' : 'forbidden'})
    response.status_code = 403
    return response

@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])
