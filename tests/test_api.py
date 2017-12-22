#-*- coding:utf-8 -*-

# 本文件重要测试 REST API 服务

import unittest
import json
from base64 import b64encode
from flask import url_for
from app import create_app, db
from app.models import User, Role

class APITestCase(unittest.TestCase):
    
    def setUp(self):
        # 创建测试app
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        # 创建测试数据库
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        # 清理数据库
        db.session.remove()
        db.drop_all()
        # 清理app context
        self.app_context.pop()

    def get_api_headers(self, username, password):
        return {
            'Authorization': 'Basic ' + b64encode(\
                    (username + ':' + password).encode('utf8')).decode('utf8'),
            'Accept' : 'application/json',
            'Content-Type': 'application/json'
            }

    def test_error_404(self):
        # 访问不存在的 api
        response = self.client.get('wrong/url',
                            headers=self.get_api_headers('email', 'password'))
        self.assertTrue(response.status_code == 404)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['error'] == 'not found')

    def test_no_auth(self):
        # 以匿名身份访问
        response = self.client.get(url_for('api.get_posts'), 
                                content_type='application/json')
        self.assertTrue(response.status_code == 200)

    def test_bad_auth(self):
        # 创建新user
        user = User(email='john@example.com', username='john',
                    password='cat', confirmed=True)
        db.session.add(user)
        db.session.commit()
        # 使用错误密码进行认证
        response = self.client.get(url_for('api.get_posts'),
                        headers=self.get_api_headers('john@example.com', 'dog'))
        self.assertTrue(response.status_code == 401)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['error'] == 'unauthorized')

    # 测试使用token进行http验证
    def test_token_auth(self):
        # 创建新用户
        user = User(email='john@example.com', username='john',
                    password='cat', confirmed=True)
        db.session.add(user)
        db.session.commit()

        # 获取认证token
        response = self.client.get(url_for('api.get_token'),
                        headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf8'))
        token_auth = json_response['token']

        # 使用token认证获取新token
        response = self.client.get(url_for('api.get_token'),
                        headers=self.get_api_headers(token_auth, ''))
        self.assertTrue(response.status_code == 401)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['error'] == 'unauthorized')

        # 使用token认证获取其他资源
        response = self.client.get(url_for('api.get_posts'),
                        headers=self.get_api_headers(token_auth, ''))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['posts'] == [])
        self.assertTrue(json_response['prev'] == None)
        self.assertTrue(json_response['next'] == None)
        self.assertTrue(json_response['count'] == 0)

    def test_unconfirmed_account(self):
        # 创建未确认的新用户
        user = User(email='john@example.com', username='john',
                    password='cat')
        db.session.add(user)
        db.session.commit()

        # 使用新账户访问posts资源
        response = self.client.get(url_for('api.get_posts'),
                        headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertTrue(response.status_code == 403)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['error'] == 'forbidden')

    def test_posts(self):
        # 创建新用户
        user = User(email='john@example.com', username='john',
                    password='cat', confirmed=True)
        db.session.add(user)
        db.session.commit()

        # 获取认证token
        response = self.client.get(url_for('api.get_token'),
                        headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf8'))
        token = json_response['token']

        # 增加一个空post
        response = self.client.post(url_for('api.new_post'),
                        headers=self.get_api_headers(token, ''),
                        data = json.dumps({'body' : ''}))
        self.assertTrue(response.status_code == 400)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['error'] == 'bad request')

        # 增加一个正常post
        response = self.client.post(
                url_for('api.new_post'),
                headers=self.get_api_headers(token, ''),
                data = json.dumps({'body' : 'This is the first post.'}))
        self.assertTrue(response.status_code == 201)
        url_post = response.headers.get('Location')
        self.assertIsNotNone(url_post)

        # 获取新增加的post
        response = self.client.get(url_post,
                headers=self.get_api_headers(token, ''))
        self.assertTrue(response.status_code == 200)
        json_data = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_data['url'] == url_post)
        self.assertTrue(json_data['body'] == 'This is the first post.')
        json_post = json_data

        # 获取该用户的post
        response = self.client.get(url_for('api.get_user_posts', id=user.id),
                headers=self.get_api_headers(token, ''))
        self.assertTrue(response.status_code == 200)
        json_data = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_data['user_posts'][0] == json_post)
        self.assertTrue(json_data['prev'] == None)
        self.assertTrue(json_data['next'] == None)
        self.assertTrue(json_data['count'] == 1)

        # 获取该用户关注的用户的post
        response = self.client.get(url_for('api.get_user_timeline', id=user.id),
                headers=self.get_api_headers(token, ''))
        self.assertTrue(response.status_code == 200)
        json_data = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_data['followed_posts'][0] == json_post)
        self.assertTrue(json_data['prev'] == None)
        self.assertTrue(json_data['next'] == None)
        self.assertTrue(json_data['count'] == 1)

        # 编辑一个存在的post
        response = self.client.put(
                url_post,
                headers=self.get_api_headers(token, ''),
                data = json.dumps({'body' : 'This post has been updated.'}))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['url'] == url_post)
        self.assertTrue(json_response['body'] == 'This post has been updated.')
        

