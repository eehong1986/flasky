#-*- coding:utf-8 -*-

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'HelloStranger'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_DEBUG = True
    MAIL_SERVER = 'smtp.qq.com'                                     # smtp��������ַ
    MAIL_PORT = 465                                                        # smtp�������˿�
    MAIL_USE_SSL = True                                                  # qq����Ҫ��ʹ�� SSL
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')     # �����û���
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')     # �û�ʶ����
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <346271437@qq.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')

    @staticmethod
    def init_app(app):
        pass

# ������������
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or \
            'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

# ���Ի�������
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI') or \
            'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')

# ������������
class ProductConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
            'sqlite:///' + os.path.join(basedir, 'data.sqlite')

config = {
    'development' : DevelopmentConfig,
    'testing' : TestingConfig,
    'product' : ProductConfig,

    'default' : DevelopmentConfig
    }
