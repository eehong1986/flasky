#-*- coding:utf-8 -*-

# 把程序实例的创建过程移到可显式调用的工厂函数中。构造文件导入了大多数正在使用的Flask
# 展，但由于尚未初始化所需的程序实例，所以没有初始化扩展，创建扩展类时没有向构造函数
# 传入参数。create_app()函数就是程序的工厂函数。

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
    
    # 初始化扩展
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)

    # 附加路由和自定义的错误页面
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # 返回创建的程序实例
    return app


