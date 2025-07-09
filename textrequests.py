from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")
import requests
import base64
from PIL import Image
from io import BytesIO

# === 用户信息 ===
user_account = '2302040203'
user_password = 'CaoBin050328'

# === URL 配置 ===
captcha_url = 'https://jwgl.yku.edu.cn/jsxsd/verifycode.servlet'
login_url = 'https://jwgl.yku.edu.cn/jsxsd/xk/LoginToXk'

# === headers ===
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36',
    'Referer': 'https://jwgl.yku.edu.cn/jsxsd/xk/LoginToXk',
    'Origin': 'https://jwgl.yku.edu.cn',
    'Content-Type': 'application/x-www-form-urlencoded'
}

# === 使用一个 Session 保证 cookie 持久 ===
session = requests.Session()

# === 第一步：获取验证码图像 ===
captcha_response = session.get(captcha_url, headers=headers, verify=False)
image = Image.open(BytesIO(captcha_response.content))
image.show()  # 自动弹出图像窗口

captcha_code = input("请输入验证码（区分大小写）：").strip()

# === 第二步：生成 encoded 字段 ===
encoded = base64.b64encode(user_account.encode()).decode() + '%%%' + base64.b64encode(user_password.encode()).decode()

# === 第三步：构造 POST 表单数据 ===
payload = {
    'userAccount': user_account,
    'userPassword': user_password,
    'RANDOMCODE': captcha_code,
    'encoded': encoded
}

# === 第四步：发起登录请求 ===
login_response = session.post(login_url, data=payload, headers=headers, verify=False)

# === 第五步：判断登录结果 ===
if "showMsg" in login_response.text:
    print("❌ 登录失败，请检查账号、密码或验证码")
else:
    print("✅ 登录成功！")

# === 可选：打印部分响应内容做调试 ===
# print(login_response.text[:500])  

import time
from bs4 import BeautifulSoup

# 成绩接口（真实返回表格的接口）
query_url = "https://jwgl.yku.edu.cn/jsxsd/kscj/cjcx_list"

# 请求参数（你可以改成 "" 或选择学期）
form_data = {
    "kksj": "2023-2024-2",  # 当前学期
    "kcxz": "10",           # 可空（如"10"代表通识选修）
    "kcmc": "",             # 可输入课程名关键词
    "xsfs": "all"           # 显示所有成绩
}

# 请求头（Referer 要指向 cjcx_query 页面）
query_headers = headers.copy()
query_headers["Referer"] = "https://jwgl.yku.edu.cn/jsxsd/kscj/cjcx_query"

# 发起 POST 请求
print("⏳ 正在请求成绩数据...")
start = time.time()
resp = session.post(query_url, data=form_data, headers=query_headers, verify=False)
end = time.time()
print(f"✅ 响应时间：{end - start:.2f} 秒")

resp.encoding = "utf-8"

# 检查是否登录失效
if "重新登录" in resp.text or "登录" in resp.text:
    print("❌ 登录状态失效，请重新登录")
    exit()

# 解析 HTML 表格
soup = BeautifulSoup(resp.text, "html.parser")

# ✅ 精确找成绩表格
table = soup.find("table", id="dataList")
if not table:
    print("❌ 没有找到成绩表格，可能是页面结构变动")
    exit()

# ✅ 提取表头
headers = [th.get_text(strip=True) for th in table.find_all("th")]
print(" | ".join(headers))

# ✅ 提取数据行
for row in table.find_all("tr")[1:]:  # 跳过表头
    cols = [td.get_text(strip=True) for td in row.find_all("td")]
    if cols and len(cols) == len(headers):
        print(" | ".join(cols))