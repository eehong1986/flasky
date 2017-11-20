#-*- coding:utf-8 -*-

# 登录表单实现

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('keep me logged in')
    submit = SubmitField('Log in')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 
                                        'Usernames must have only letters, '
                                        'numbers, dots or underscores')])
    password = PasswordField('Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

# 用户修改账户密码的表单 要求输入旧密码，新密码和确认新密码
class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[Required()])
    password = PasswordField('New Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm New Password', validators=[Required()]) 
    submit = SubmitField('Update Password')

# 要求用户输入email，向用户发送token邮件
class PasswordResetRequestForm(FlaskForm):
     email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
     submit = SubmitField('Reset Password')

# 引导用户设置新密码
class PasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('New Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm New Password', validators=[Required()]) 
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')

# 修改用户email
class ChangeEmailForm(FlaskForm):
    email = StringField('New Email', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')
