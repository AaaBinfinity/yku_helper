import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from .utils.session_handler import login_and_get_session, get_captcha_base64
from .utils.grade_parser import get_grades
from .utils.student_lookup import get_student_name
from .utils.askai import ask_ai
import requests

# 日志配置
log_dir = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "login.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)

grades_logger = logging.getLogger("grades_logger")
grades_logger.setLevel(logging.INFO)
if not grades_logger.hasHandlers():
    grades_handler = logging.FileHandler(os.path.join(log_dir, "grades.log"), encoding="utf-8")
    grades_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    grades_logger.addHandler(grades_handler)

main = Blueprint("main", __name__)

# ========== 路由实现 ==========
@main.route("/", methods=["GET", "POST"])
def login():
    
    img_base64, cookies = get_captcha_base64()
    session["captcha_cookies"] = cookies
    return render_template("login.html", captcha=img_base64)


@main.route("/grades")
def grades():
    if "cookies" not in session:
        return redirect(url_for("main.login"))
    return render_template("grades.html")


@main.route("/home")
def home():
    username = session.get("username")
    student_name = session.get("student_name")

    if not username:
        return redirect(url_for("main.login"))

    return render_template("home.html", username=username, student_name=student_name)


@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/api/captcha")
def captcha():
    img_base64, cookies = get_captcha_base64()
    session["captcha_cookies"] = cookies
    return jsonify({"captcha": img_base64})


@main.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    captcha_code = data.get("captcha", "").strip()
    captcha_cookies = session.get("captcha_cookies", {})

    student_name = get_student_name(username)
    logging.info(f"📥 API登录尝试 - 学号: {username}, 姓名: {student_name}")

    user_session = login_and_get_session(username, password, captcha_code, captcha_cookies)
    if not user_session:
        return jsonify({"success": False, "msg": "登录失败"}), 401

    session["username"] = username
    session["student_name"] = student_name
    session["cookies"] = user_session.cookies.get_dict()

    return jsonify({"success": True, "msg": "登录成功", "student_name": student_name})


@main.route("/api/grades")
def api_grades():
    if "cookies" not in session:
        return jsonify({"success": False, "msg": "未登录"}), 401

    user_session = requests.Session()
    user_session.cookies.update(session["cookies"])

    kksj = request.args.get("kksj", "")
    kcxz = request.args.get("kcxz", "")
    kcmc = request.args.get("kcmc", "")
    xsfs = request.args.get("xsfs", "all")

    grades_data = get_grades(user_session, kksj=kksj, kcxz=kcxz, kcmc=kcmc, xsfs=xsfs)
    sno = session.get("username", "未知学号")
    sname = session.get("student_name", "未知姓名")

    grades_logger.info(
        f"✅ 成绩查询 - 学号: {sno}, 姓名: {sname}, "
        f"开课学期: '{kksj}', 课程性质: '{kcxz}', 课程名称关键词: '{kcmc}', 显示方式: '{xsfs}', "
        f"记录数: {len(grades_data)}"
    )

    return jsonify({
        "success": True,
        "data": {
            "sno": sno,
            "sname": sname,
            "grades": grades_data
        }
    })


@main.route("/api/aigrades")
def analyze_grades_auto():
    if "cookies" not in session:
        return jsonify({"success": False, "message": "未登录"}), 401

    user_session = requests.Session()
    user_session.cookies.update(session["cookies"])

    kksj = request.args.get("kksj", "")
    kcxz = request.args.get("kcxz", "")
    kcmc = request.args.get("kcmc", "")
    xsfs = request.args.get("xsfs", "all")

    grades = get_grades(user_session, kksj, kcxz, kcmc, xsfs)
    sno = session.get("username", "未知学号")
    sname = session.get("student_name", "未知姓名")

    if not grades:
        return jsonify({"success": False, "message": "没有找到成绩数据"}), 404

    log_text = f"分析一下{sname}同学的成绩\n\n📋 查询到 {len(grades)} 条记录\n"
    for item in grades:
        log_text += (
            f"课程: {item.get('课程名称')}｜成绩: {item.get('成绩')}｜学分: {item.get('学分')}｜"
            f"学期: {item.get('开课学期')}｜补重: {item.get('补重学期')}｜"
            f"考核: {item.get('考核方式')}｜考试性质: {item.get('考试性质')}｜"
            f"课程属性: {item.get('课程属性')}｜课程性质: {item.get('课程性质')}\n"
        )

    prompt = f"""你是一个教育顾问，请分析以下成绩内容：
1. 整体成绩表现如何？是否存在短板？
2. 哪些课程优秀，哪些不理想？
3. 是否存在挂科/补考现象？
4. 一句建议。

成绩如下：
{log_text}
"""
    try:
        result = ask_ai(prompt)
        return jsonify({"success": True, "sno": sno, "sname": sname, "analysis": result})
    except Exception as e:
        return jsonify({"success": False, "message": f"分析失败: {str(e)}"}), 500
