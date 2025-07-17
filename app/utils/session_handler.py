import requests
import base64
import uuid
import logging
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(parent_dir)

from config import *
import redis

rds = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    username=Config.REDIS_USERNAME,
    password=Config.REDIS_PASSWORD,
    db=Config.REDIS_DB,
    decode_responses=True
)

# 日志路径配置
log_dir = os.path.join(os.path.dirname(__file__), '../log')
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, 'login.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_path, encoding='utf-8'),
        logging.StreamHandler()
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


def get_captcha_base64_with_key():
    """
    获取验证码 base64 编码并生成唯一 key 存入 Redis（保存 session cookies）
    :return: (base64_str, uuid_key)
    """
    session = requests.Session()
    response = session.get(captcha_url, headers=HEADERS, verify=False)
    img_base64 = base64.b64encode(response.content).decode()

    key = str(uuid.uuid4())

    rds.setex(f"captcha:{key}", 120, str(session.cookies.get_dict()))

    # logging.info(f"🧩 获取验证码 - Key: {key}")
    return img_base64, key


def login_by_key(user_account, user_password, captcha_code, key):
    """
    使用验证码 key 从 Redis 中取出 cookies，然后尝试登录
    """
    cookies_str = rds.get(f"captcha:{key}")
    if not cookies_str:
        logging.warning(f"❌ 登录失败 - Redis中未找到验证码 Key: {key}")
        return None

    try:
        cookies_dict = eval(cookies_str)
    except Exception as e:
        logging.warning(f"❌ 登录失败 - Cookies格式解析异常: {e}")
        return None

    logging.info(f"===================登录尝试 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}=====================")

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
    
    # 调试输出响应内容（生产环境可移除）
    logging.debug(f"登录响应状态码: {response.status_code}")
    logging.debug(f"登录响应URL: {response.url}")
    
    # 基本响应状态检查
    if response.status_code != 200:
        logging.warning(f"❌ 登录失败 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}")
        return None
        
    # 检查明确的失败标志
    if "showMsg" in response.text:
        logging.warning(f"❌ 登录失败 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}")
        return None
        
    # 检查是否停留在登录页面
    if "LoginToXk" in response.url:
        logging.warning(f"❌ 登录失败 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}")
        return None
        
    # 检查是否有明确的成功标志
    success_indicators = [
        "main.jsp",  # 主页面
        "xsMain.jsp",  # 学生主页面
        "欢迎您",  # 欢迎信息
        "学生个人中心",  # 个人中心标题
        user_account  # 学号出现在页面中
    ]
    
    # 只要满足任一成功标志即认为登录成功
    if any(indicator in response.text for indicator in success_indicators):
        logging.info(f"✅ 登录成功 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}")
        return session
    else:
        logging.warning(f"❌ 登录失败 - 未识别到成功标志 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}")
        return None