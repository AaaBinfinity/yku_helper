import requests
import base64
from io import BytesIO
from PIL import Image
import logging
captcha_url = 'https://jwgl.yku.edu.cn/jsxsd/verifycode.servlet'
login_url = 'https://jwgl.yku.edu.cn/jsxsd/xk/LoginToXk'

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': login_url,
    'Origin': 'https://jwgl.yku.edu.cn',
    'Content-Type': 'application/x-www-form-urlencoded'
}

# 持久化 session（跨函数）
session = requests.Session()

def get_captcha_base64():
    response = session.get(captcha_url, headers=HEADERS, verify=False)
    image_data = BytesIO(response.content)
    img_base64 = base64.b64encode(image_data.getvalue()).decode()
    return img_base64

def login_and_get_session(user_account, user_password, captcha_code):

    # logging.info(f"登录函数调用 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}")
    # logging.info(f"===================登录尝试 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}=====================")
    encoded = base64.b64encode(user_account.encode()).decode() + '%%%' + base64.b64encode(user_password.encode()).decode()
    
    payload = {
        'userAccount': user_account,
        'userPassword': user_password,
        'RANDOMCODE': captcha_code,
        'encoded': encoded
    }

    response = session.post(login_url, headers=HEADERS, data=payload, verify=False)

    if "showMsg" in response.text:
        # logging.warning(f"❌ 登录失败 - 学号: {user_account}")
        return None

    # logging.info(f"✅ 登录成功 - 学号: {user_account}")
    return session