#-*- coding:utf-8 -*-

# 使用Flask自带的客户端测试视图函数

import unittest
import re
from flask import url_for
from app import create_app, db
from app.models import User, Role

class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        # 创建 app
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        # 创建数据库
        db.create_all()
        Role.insert_roles()
        # 记录客户端
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        # 清理数据库
        db.session.remove()
        db.drop_all()
        # 清理app context
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get(url_for('main.index'))
        self.assertTrue('Stranger' in response.get_data(as_text=True))
    
    def test_register_and_login(self):
        # 注册新用户
        response = self.client.post(url_for('auth.register'), data={
                        'email' : 'john@example.com',
                        'username' : 'john',
                        'password' : 'cat',
                        'password2': 'cat'})
        # 注册成功应重定向到home页
        self.assertTrue(response.status_code == 302)

        # 使用新注册的账户登录
        response = self.client.post(url_for('auth.login'), data = {
                        'email' : 'john@example.com', 
                        'password' : 'cat'
                        }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue(re.search('Hello,\s*john!', data))
        self.assertTrue('You have not confirmed your account yet' in data)

        # 发送确认令牌 忽略注册时的令牌，重新生成令牌并进行确认
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get(url_for('auth.confirm', token=token),
                                follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue('You have confirmed your account' in data)

        # 退出
        response = self.client.get(url_for('auth.logout'), 
                                follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue('You have been logged out' in data)

    def test_user_profile(self):
        # 创建一个新用户
        user = User(email='john@example.com', username='john', 
                    password='cat', confirmed=True)
        db.session.add(user)
        db.session.commit()
        # 新用户登录
        response = self.client.post(url_for('auth.login'), data={
                        'email' : 'john@example.com',
                        'password': 'cat'
                        }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue(re.search('Hello,\s*john', data))
        # 进入用户profile页面
        response = self.client.get(url_for('main.user', 
                                            username=user.username)) 
        data=response.get_data(as_text=True)
        self.assertTrue('john' in data)
        self.assertTrue('Edit Profile' in data)

        # 更新用户profile
        response = self.client.post(url_for('main.edit_profile'), data={
                            'username': user.username,
                            'location': 'Beijing, China',
                            'about_me': 'A python beginner'
                            }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue('Your profile has been updated' in data)

    def test_post(self):
        # 创建新用户
        user = User(email='john@example.com', username='john', 
                    password='cat', confirmed=True)
        db.session.add(user)
        db.session.commit()

        # 新账户登录
        response = self.client.post(url_for('auth.login'), data={
                            'email' : 'john@example.com',
                            'password': 'cat'
                            }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue(re.search('Hello,\s*john', data))

        # 添加新文章post
        response = self.client.post(url_for('main.index'), data={
                            'body' : "I'm adding a new post."
                            }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue("I'm adding a new post." in data)
        self.assertTrue(user.posts.count() == 1)

        # 访问新post
        response = self.client.get(url_for('main.post', id=1))
        data = response.get_data(as_text=True)
        self.assertTrue('john' in data)
        self.assertTrue(re.search('0\s*Comments', data))

        # 为post添加comment
        response = self.client.post(url_for('main.post', id=1), data={
                            'body' : 'This is the first comment.'
                            }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue('Your comment has been published.' in data)
        self.assertTrue(re.search('1\s*Comments', data))


