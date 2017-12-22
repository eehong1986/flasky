#-*- coding:utf-8 -*-

# ���ļ���Ҫ���� REST API ����

import unittest
import json
from base64 import b64encode
from flask import url_for
from app import create_app, db
from app.models import User, Role

class APITestCase(unittest.TestCase):
    
    def setUp(self):
        # ��������app
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        # �����������ݿ�
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        # �������ݿ�
        db.session.remove()
        db.drop_all()
        # ����app context
        self.app_context.pop()

    def get_api_headers(self, username, password):
        return {
            'Authorization': 'Basic ' + b64encode(\
                    (username + ':' + password).encode('utf8')).decode('utf8'),
            'Accept' : 'application/json',
            'Content-Type': 'application/json'
            }

    def test_error_404(self):
        # ���ʲ����ڵ� api
        response = self.client.get('wrong/url',
                            headers=self.get_api_headers('email', 'password'))
        self.assertTrue(response.status_code == 404)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['error'] == 'not found')

    def test_no_auth(self):
        # ��������ݷ���
        response = self.client.get(url_for('api.get_posts'), 
                                content_type='application/json')
        self.assertTrue(response.status_code == 200)

    def test_bad_auth(self):
        # ������user
        user = User(email='john@example.com', username='john',
                    password='cat', confirmed=True)
        db.session.add(user)
        db.session.commit()
        # ʹ�ô������������֤
        response = self.client.get(url_for('api.get_posts'),
                        headers=self.get_api_headers('john@example.com', 'dog'))
        self.assertTrue(response.status_code == 401)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['error'] == 'unauthorized')

    # ����ʹ��token����http��֤
    def test_token_auth(self):
        # �������û�
        user = User(email='john@example.com', username='john',
                    password='cat', confirmed=True)
        db.session.add(user)
        db.session.commit()

        # ��ȡ��֤token
        response = self.client.get(url_for('api.get_token'),
                        headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf8'))
        token_auth = json_response['token']

        # ʹ��token��֤��ȡ��token
        response = self.client.get(url_for('api.get_token'),
                        headers=self.get_api_headers(token_auth, ''))
        self.assertTrue(response.status_code == 401)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['error'] == 'unauthorized')

        # ʹ��token��֤��ȡ������Դ
        response = self.client.get(url_for('api.get_posts'),
                        headers=self.get_api_headers(token_auth, ''))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['posts'] == [])
        self.assertTrue(json_response['prev'] == None)
        self.assertTrue(json_response['next'] == None)
        self.assertTrue(json_response['count'] == 0)

    def test_unconfirmed_account(self):
        # ����δȷ�ϵ����û�
        user = User(email='john@example.com', username='john',
                    password='cat')
        db.session.add(user)
        db.session.commit()

        # ʹ�����˻�����posts��Դ
        response = self.client.get(url_for('api.get_posts'),
                        headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertTrue(response.status_code == 403)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['error'] == 'forbidden')

    def test_posts(self):
        # �������û�
        user = User(email='john@example.com', username='john',
                    password='cat', confirmed=True)
        db.session.add(user)
        db.session.commit()

        # ��ȡ��֤token
        response = self.client.get(url_for('api.get_token'),
                        headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf8'))
        token = json_response['token']

        # ����һ����post
        response = self.client.post(url_for('api.new_post'),
                        headers=self.get_api_headers(token, ''),
                        data = json.dumps({'body' : ''}))
        self.assertTrue(response.status_code == 400)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['error'] == 'bad request')

        # ����һ������post
        response = self.client.post(
                url_for('api.new_post'),
                headers=self.get_api_headers(token, ''),
                data = json.dumps({'body' : 'This is the first post.'}))
        self.assertTrue(response.status_code == 201)
        url_post = response.headers.get('Location')
        self.assertIsNotNone(url_post)

        # ��ȡ�����ӵ�post
        response = self.client.get(url_post,
                headers=self.get_api_headers(token, ''))
        self.assertTrue(response.status_code == 200)
        json_data = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_data['url'] == url_post)
        self.assertTrue(json_data['body'] == 'This is the first post.')
        json_post = json_data

        # ��ȡ���û���post
        response = self.client.get(url_for('api.get_user_posts', id=user.id),
                headers=self.get_api_headers(token, ''))
        self.assertTrue(response.status_code == 200)
        json_data = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_data['user_posts'][0] == json_post)
        self.assertTrue(json_data['prev'] == None)
        self.assertTrue(json_data['next'] == None)
        self.assertTrue(json_data['count'] == 1)

        # ��ȡ���û���ע���û���post
        response = self.client.get(url_for('api.get_user_timeline', id=user.id),
                headers=self.get_api_headers(token, ''))
        self.assertTrue(response.status_code == 200)
        json_data = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_data['followed_posts'][0] == json_post)
        self.assertTrue(json_data['prev'] == None)
        self.assertTrue(json_data['next'] == None)
        self.assertTrue(json_data['count'] == 1)

        # �༭һ�����ڵ�post
        response = self.client.put(
                url_post,
                headers=self.get_api_headers(token, ''),
                data = json.dumps({'body' : 'This post has been updated.'}))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf8'))
        self.assertTrue(json_response['url'] == url_post)
        self.assertTrue(json_response['body'] == 'This post has been updated.')
        

