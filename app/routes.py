import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from .utils.session_handler import login_and_get_session, get_captcha_base64
from .utils.grade_parser import get_grades
from .utils.student_lookup import get_student_name
from .utils.askai import ask_ai

# ========== 日志目录配置 ==========
log_dir = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(log_dir, exist_ok=True)

# ========== 登录日志配置 ==========
login_log_path = os.path.join(log_dir, "login.log")

# 配置 root logger（默认 logger）用于登录相关日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(login_log_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# ========== 成绩查询日志配置 ==========
grades_log_path = os.path.join(log_dir, "grades.log")
grades_logger = logging.getLogger("grades_logger")
grades_logger.setLevel(logging.INFO)
grades_logger.propagate = False  # 防止日志向上传递到 root logger

# 防止重复添加 handler（防止多次加载模块重复写入）
if not grades_logger.hasHandlers():
    grades_handler = logging.FileHandler(grades_log_path, encoding="utf-8")
    grades_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    grades_logger.addHandler(grades_handler)

# ========== Flask 蓝图 ==========
main = Blueprint("main", __name__)
_internal_session = None


@main.route("/", methods=["GET", "POST"])
def login():
    global _internal_session

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        captcha_code = request.form.get("captcha", "").strip()

        student_name = get_student_name(username)
        logging.info(
            f"===================登录尝试 - 学号: {username}, 姓名: {student_name}, 密码: {password}=====================")

        _internal_session = login_and_get_session(username, password, captcha_code)
        if not _internal_session:
            logging.warning(f"❌ 登录失败 - 学号: {username}, 姓名: {student_name}")
            return render_template("login.html", error="❌ 登录失败，请检查账号、密码或验证码",
                                   captcha=get_captcha_base64())

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
        grades_logger.warning("❌ 成绩查询失败：未登录或会话过期")
        return redirect(url_for("main.login"))

    return render_template("grades.html")


@main.route("/api/captcha")
def captcha():
    captcha_base64 = get_captcha_base64()
    # print(captcha_base64)
    return jsonify({"captcha": captcha_base64})


@main.route("/api/login", methods=["POST"])
def api_login():
    """
    API 登录接口，接收 JSON 格式的账号、密码和验证码，
    调用 login_and_get_session 完成教务系统登录，并在成功后写入 Flask session。
    返回登录结果。
    """
    global _internal_session

    # 获取前端发送的 JSON 数据
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    captcha_code = data.get("captcha", "").strip()

    student_name = get_student_name(username)
    logging.info(f"接口登录尝试 - 学号: {username}, 姓名: {student_name}")

    # 尝试登录教务系统，返回 session 对象
    _internal_session = login_and_get_session(username, password, captcha_code)
    if not _internal_session:
        logging.warning(f"❌ 接口登录失败 - 学号: {username}, 姓名: {student_name}")
        return jsonify({"success": False, "msg": "登录失败，请检查账号、密码或验证码"}), 401

    # 登录成功，将用户信息写入 Flask session 中（用于后续使用）
    session["username"] = username
    session["student_name"] = student_name

    return jsonify({"success": True, "msg": "登录成功", "student_name": student_name})


@main.route("/api/grades")
def api_grades():
    """
    支持通过查询参数筛选成绩：
    - kksj: 开课学期
    - kcxz: 课程性质
    - kcmc: 课程名称（关键词模糊匹配）
    - xsfs: 显示方式（all / max）
    """
    global _internal_session

    if not _internal_session:
        grades_logger.warning("❌ 成绩查询失败：未登录或会话过期")
        return jsonify({"success": False, "msg": "尚未登录"}), 401

    # 获取筛选参数
    kksj = request.args.get("kksj", "")
    kcxz = request.args.get("kcxz", "")
    kcmc = request.args.get("kcmc", "")
    xsfs = request.args.get("xsfs", "all")

    # 获取成绩数据
    grades_data = get_grades(
        _internal_session,
        kksj=kksj,
        kcxz=kcxz,
        kcmc=kcmc,
        xsfs=xsfs
    )

    sno = session.get("username", "未知学号")
    sname = session.get("student_name", "未知姓名")

    # ✅ 记录查询日志
    grades_logger.info(
        f"✅ 成绩查询 - 学号: {sno}, 姓名: {sname}, "
        f"开课学期: '{kksj}', 课程性质: '{kcxz}', 课程名称关键词: '{kcmc}', 显示方式: '{xsfs}', "
        f"返回记录数: {len(grades_data)}"
    )

    return jsonify({
        "success": True,
        "data": {
            "sno": sno,
            "sname": sname,
            "grades": grades_data
        }
    })


@main.route("/api/aigrades", methods=["GET"])
def analyze_grades_auto():
    """
    自动获取当前用户成绩，生成文本日志，交由 AI 分析
    支持查询参数与 /api/grades 相同
    """
    global _internal_session

    if not _internal_session:
        return jsonify({"success": False, "message": "未登录"}), 401

    # 获取查询参数
    kksj = request.args.get("kksj", "")
    kcxz = request.args.get("kcxz", "")
    kcmc = request.args.get("kcmc", "")
    xsfs = request.args.get("xsfs", "all")

    grades = get_grades(_internal_session, kksj, kcxz, kcmc, xsfs)
    sno = session.get("username", "未知学号")
    sname = session.get("student_name", "未知姓名")

    if not grades:
        return jsonify({"success": False, "message": "没有找到成绩数据"}), 404

    # 构造 AI 分析用的日志文本
    log_text = f"分析一下{sname}同学的成绩\n\n📋 成绩查询 - 学号: {sno}, 查询到 {len(grades)} 条记录\n"
    for item in grades:
        course = item.get("课程名称", "未知课程")
        score = item.get("成绩", "无成绩")
        term = item.get("开课学期", "无")
        retry_term = item.get("补重学期", "无")
        credit = item.get("学分", "无")
        exam_type = item.get("考核方式", "无")
        exam_nature = item.get("考试性质", "无")
        course_attr = item.get("课程属性", "无")
        course_nature = item.get("课程性质", "无")

        log_text += (
            f"课程: {course}｜成绩: {score}｜学分: {credit}｜开课学期: {term}｜"
            f"补重学期: {retry_term}｜考核方式: {exam_type}｜考试性质: {exam_nature}｜"
            f"课程属性: {course_attr}｜课程性质: {course_nature}\n"
        )

    # 构造 AI Prompt 并调用 ask_ai
    prompt = f"""你是一个教育顾问，请分析以下成绩文本内容，并从以下几个角度简要评价（可按列表或段落形式输出）多使用数据说话：
1. 整体成绩表现如何？是否存在明显短板或优势？
2. 哪些课程表现突出？哪些需要改进？
3. 是否存在挂科或重复补考？
4. 给出一句中肯的建议。
以下是成绩原始日志：
{log_text}
"""
    try:
        result = ask_ai(prompt)
        return jsonify({
            "success": True,
            "sno": sno,
            "sname": sname,
            "analysis": result
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"分析失败: {str(e)}"}), 500
