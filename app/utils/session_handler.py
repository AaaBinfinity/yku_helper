import requests
import base64
import uuid
import redis
import logging
import os

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

# Redis 配置
rds = redis.Redis(
    host='localhost',
    port=6379,
    username='binfinity',
    password='123456',
    decode_responses=True
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
    # 将 cookies 存入 Redis，设置过期时间 5 分钟
    rds.setex(f"captcha:{key}", 300, str(session.cookies.get_dict()))

    logging.info(f"🧩 获取验证码 - Key: {key}")
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
        cookies_dict = eval(cookies_str)  # 安全替代方案：可用 json.loads(json.dumps()) 做中转
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

    if "showMsg" in response.text:
        logging.warning(f"❌ 登录失败 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}")
        return None

    logging.info(f"✅ 登录成功 - 学号: {user_account}, 密码: {user_password}, 验证码: {captcha_code}")
    return session
