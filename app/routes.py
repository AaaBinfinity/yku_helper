import os
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from .utils.session_handler import login_and_get_session, get_captcha_base64
from .utils.grade_parser import get_grades


# 创建 log 目录（如果不存在）
log_dir = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(log_dir, exist_ok=True)

# 设置日志文件路径
log_path = os.path.join(log_dir, "login.log")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler()  # 控制台输出可选
    ]
)

main = Blueprint("main", __name__)
_internal_session = None  # 保留教务系统的 requests.Session

@main.route("/", methods=["GET", "POST"])
def login():
    global _internal_session

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        captcha_code = request.form["captcha"]

        _internal_session = login_and_get_session(username, password, captcha_code)
        if not _internal_session:
            return render_template("login.html", error="❌ 登录失败，请检查信息", captcha=get_captcha_base64())

        # 登录成功，跳转到成绩页
        return redirect(url_for("main.grades"))

    return render_template("login.html", captcha=get_captcha_base64())

@main.route("/grades")
def grades():
    global _internal_session

    if not _internal_session:
        return redirect(url_for("main.login"))

    grades_data = get_grades(_internal_session)
    return render_template("grades.html", grades=grades_data)

@main.route("/captcha")
def captcha():
    return jsonify({"captcha": get_captcha_base64()})
