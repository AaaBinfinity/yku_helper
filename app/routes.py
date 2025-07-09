import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from .utils.session_handler import login_and_get_session, get_captcha_base64
from .utils.grade_parser import get_grades
from .utils.student_lookup import get_student_name

# ========== 日志配置 ==========
log_dir = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(log_dir, exist_ok=True)

log_path = os.path.join(log_dir, "login.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# ========== Flask 蓝图 ==========
main = Blueprint("main", __name__)
_internal_session = None  # 保留教务系统 requests.Session

@main.route("/", methods=["GET", "POST"])
def login():
    global _internal_session

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        captcha_code = request.form.get("captcha", "").strip()

        student_name = get_student_name(username)
        logging.info(f"登录尝试 - 学号: {username}, 姓名: {student_name}, 密码: {password}")

        _internal_session = login_and_get_session(username, password, captcha_code)
        if not _internal_session:
            logging.warning(f"❌ 登录失败 - 学号: {username}, 姓名: {student_name}")
            return render_template("login.html", error="❌ 登录失败，请检查账号、密码或验证码", captcha=get_captcha_base64())

        # ✅ 登录成功后记录用户信息到 Flask session
        session["username"] = username
        session["student_name"] = student_name

        logging.info(f"✅ 登录成功 - 学号: {username}, 姓名: {student_name}")
        return redirect(url_for("main.grades"))

    return render_template("login.html", captcha=get_captcha_base64())

@main.route("/grades")
def grades():
    global _internal_session

    if not _internal_session:
        return redirect(url_for("main.login"))

    grades_data = get_grades(_internal_session)

    # ✅ 从 Flask session 中读取学号与姓名
    sno = session.get("username", "未知学号")
    sname = session.get("student_name", "未知姓名")

    return render_template("grades.html", grades=grades_data, sno=sno, sname=sname)

@main.route("/captcha")
def captcha():
    captcha_base64 = get_captcha_base64()
    print(captcha_base64)  # 可用于调试
    return jsonify({"captcha": captcha_base64})

