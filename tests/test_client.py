#-*- coding:utf-8 -*-

# ʹ��Flask�Դ��Ŀͻ��˲�����ͼ����

import unittest
import re
from flask import url_for
from app import create_app, db
from app.models import User, Role

class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        # ���� app
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        # �������ݿ�
        db.create_all()
        Role.insert_roles()
        # ��¼�ͻ���
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        # �������ݿ�
        db.session.remove()
        db.drop_all()
        # ����app context
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get(url_for('main.index'))
        self.assertTrue('Stranger' in response.get_data(as_text=True))
    
    def test_register_and_login(self):
        # ע�����û�
        response = self.client.post(url_for('auth.register'), data={
                        'email' : 'john@example.com',
                        'username' : 'john',
                        'password' : 'cat',
                        'password2': 'cat'})
        # ע��ɹ�Ӧ�ض���homeҳ
        self.assertTrue(response.status_code == 302)

        # ʹ����ע����˻���¼
        response = self.client.post(url_for('auth.login'), data = {
                        'email' : 'john@example.com', 
                        'password' : 'cat'
                        }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue(re.search('Hello,\s*john!', data))
        self.assertTrue('You have not confirmed your account yet' in data)

        # ����ȷ������ ����ע��ʱ�����ƣ������������Ʋ�����ȷ��
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get(url_for('auth.confirm', token=token),
                                follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue('You have confirmed your account' in data)

        # �˳�
        response = self.client.get(url_for('auth.logout'), 
                                follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue('You have been logged out' in data)

    def test_user_profile(self):
        # ����һ�����û�
        user = User(email='john@example.com', username='john', 
                    password='cat', confirmed=True)
        db.session.add(user)
        db.session.commit()
        # ���û���¼
        response = self.client.post(url_for('auth.login'), data={
                        'email' : 'john@example.com',
                        'password': 'cat'
                        }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue(re.search('Hello,\s*john', data))
        # �����û�profileҳ��
        response = self.client.get(url_for('main.user', 
                                            username=user.username)) 
        data=response.get_data(as_text=True)
        self.assertTrue('john' in data)
        self.assertTrue('Edit Profile' in data)

        # �����û�profile
        response = self.client.post(url_for('main.edit_profile'), data={
                            'username': user.username,
                            'location': 'Beijing, China',
                            'about_me': 'A python beginner'
                            }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue('Your profile has been updated' in data)

    def test_post(self):
        # �������û�
        user = User(email='john@example.com', username='john', 
                    password='cat', confirmed=True)
        db.session.add(user)
        db.session.commit()

        # ���˻���¼
        response = self.client.post(url_for('auth.login'), data={
                            'email' : 'john@example.com',
                            'password': 'cat'
                            }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue(re.search('Hello,\s*john', data))

        # ���������post
        response = self.client.post(url_for('main.index'), data={
                            'body' : "I'm adding a new post."
                            }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue("I'm adding a new post." in data)
        self.assertTrue(user.posts.count() == 1)

        # ������post
        response = self.client.get(url_for('main.post', id=1))
        data = response.get_data(as_text=True)
        self.assertTrue('john' in data)
        self.assertTrue(re.search('0\s*Comments', data))

        # Ϊpost���comment
        response = self.client.post(url_for('main.post', id=1), data={
                            'body' : 'This is the first comment.'
                            }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue('Your comment has been published.' in data)
        self.assertTrue(re.search('1\s*Comments', data))


