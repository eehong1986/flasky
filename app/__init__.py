#-*- coding:utf-8 -*-

# �ѳ���ʵ���Ĵ��������Ƶ�����ʽ���õĹ��������С������ļ������˴��������ʹ�õ�Flask
# չ����������δ��ʼ������ĳ���ʵ��������û�г�ʼ����չ��������չ��ʱû�����캯��
# ���������create_app()�������ǳ���Ĺ���������

from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # ��ʼ����չ
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)

    # ����·�ɺ��Զ���Ĵ���ҳ��
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # ���ش����ĳ���ʵ��
    return app


