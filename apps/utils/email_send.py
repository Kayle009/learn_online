# coding: utf-8
from random import Random
from django.core.mail import send_mail

from users.models import EmailVerifyRecord
from learn_online.settings import EMAIL_FROM


def send_register_email(email, send_type='register'):
    email_record = EmailVerifyRecord()
    rendom_str = generate_random_str(16)
    email_record.code = rendom_str
    email_record.email = email
    email_record.send_type = send_type
    email_record.save()

    email_title = ''
    email_body = ''

    if send_type == 'register':
        email_title = '注册链接'
        email_body = '请点击下面的链接激活账号：http://127.0.0.1:8000/active/{}'.format(email_record.code)

        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
        if send_status:
            pass

    elif send_type == 'forget':
        email_title = '重置密码'
        email_body = '请点击下面的链接重置密码：http://127.0.0.1:8000/reset/{}'.format(email_record.code)

        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
        if send_status:
            pass

    elif send_type == 'update_email':
        email_title = '修改邮箱'
        email_body = '您的邮箱验证码为:{}'.format(email_record.code)

        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
        if send_status:
            pass


def generate_random_str(randomlenght=8):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    random = Random()
    charslenght = len(chars) - 1
    for i in range(randomlenght):
        str += chars[random.randint(0, charslenght)]
    return str
