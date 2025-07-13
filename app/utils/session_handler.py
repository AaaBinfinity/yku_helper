import requests
import base64
from io import BytesIO
from PIL import Image
import logging
import os

# 日志路径配置
log_dir = os.path.join(os.path.dirname(__file__), '../log')
os.makedirs(log_dir, exist_ok=True)  # 如果目录不存在则创建
log_path = os.path.join(log_dir, 'login.log')

# 配置日志输出到文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_path, encoding='utf-8'),
        logging.StreamHandler()  # 同时输出到控制台（可选）
    ]
)

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

    # 创建一个 requests.Session 对象
    session = requests.Session()
    # 更新 session cookies
    session.cookies.update(cookies_dict)

    # 将账号和密码进行 base64 编码
    encoded = base64.b64encode(user_account.encode()).decode() + '%%%' + base64.b64encode(user_password.encode()).decode()

    # 构造登录请求的 payload
    payload = {
        'userAccount': user_account,
        'userPassword': user_password,
        'RANDOMCODE': captcha_code,
        'encoded': encoded
    }

    # 发送登录请求
    response = session.post(login_url, headers=HEADERS, data=payload, verify=False)

    # 如果登录失败，返回 None
    if "showMsg" in response.text:
        logging.warning(f"❌ 登录失败 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}")
        return None

    # 如果登录成功，返回已登录的 session 对象
    logging.info(f"✅ 登录成功 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}")
    return session
