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

def get_captcha_base64():
    """
    获取验证码图片的 base64 编码，以及对应 session 的 cookies
    （由于验证码请求也需要建立 session，我们将其返回）
    """
    session = requests.Session()
    response = session.get(captcha_url, headers=HEADERS, verify=False)
    img_base64 = base64.b64encode(response.content).decode()
    return img_base64, session.cookies.get_dict()


def login_and_get_session(user_account, user_password, captcha_code, cookies_dict):
    """
    用于登录教务系统，接收账号、密码、验证码和 session cookies。
    若登录成功，返回已登录的 requests.Session 对象。
    """
    logging.info(f"===================登录尝试 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}=====================")

    # 创建新的 session 并恢复之前的 cookies（验证码时建立）
    session = requests.Session()
    session.cookies.update(cookies_dict)

    encoded = base64.b64encode(user_account.encode()).decode() + '%%%' + base64.b64encode(user_password.encode()).decode()

    payload = {
        'userAccount': user_account,
        'userPassword': user_password,
        'RANDOMCODE': captcha_code,
        'encoded': encoded
    }

    response = session.post(login_url, headers=HEADERS, data=payload, verify=False)

    if "showMsg" in response.text:
        logging.warning(f"❌ 登录失败 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}")
        return None

    logging.info(f"✅ 登录成功 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}")
    return session
