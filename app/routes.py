from functools import wraps
import os
import logging
from flask import Blueprint, abort, flash, render_template, request, redirect, send_from_directory, url_for, session, jsonify
import redis
from app.utils.resources import add_resource, get_all_resources, get_resource_by_id
from .utils.session_handler import login_by_key, get_captcha_base64_with_key
from .utils.grade_parser import get_grades
from .utils.student_lookup import get_student_name
from .utils.askai import ask_ai
import requests
from flask import jsonify
from app.utils.announcements import get_all_announcements

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

def get_user_session(username):
    """从Redis获取用户session"""
    cookies_str = rds.get(f"user_session:{username}")
    if not cookies_str:
        return None
    
    try:
        cookies_dict = eval(cookies_str)
        user_session = requests.Session()
        user_session.cookies.update(cookies_dict)
        return user_session
    except Exception as e:
        logging.error(f"Failed to restore session for {username}: {str(e)}")
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return jsonify({"success": False, "msg": "未登录"}), 401
            
        username = session["username"]
        if not rds.exists(f"user_session:{username}"):
            return jsonify({"success": False, "msg": "会话已过期，请重新登录"}), 401
            
        return f(*args, **kwargs)
    return decorated_function
# ========== 路由实现 ==========
@main.route("/", methods=["GET", "POST"])
def login():
    img_base64, captcha_key = get_captcha_base64_with_key()
    session["captcha_key"] = captcha_key
    return render_template("login.html", captcha=img_base64)


@main.route("/grades")
def grades():
    if "username" not in session:
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
    img_base64, captcha_key = get_captcha_base64_with_key()
    session["captcha_key"] = captcha_key
    return jsonify({"captcha": img_base64, "key": captcha_key})


@main.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    captcha_code = data.get("captcha", "").strip()
    captcha_key = session.get("captcha_key")

    if not captcha_key:
        logging.warning(f"登录失败: 验证码KEY不存在 - 学号: {username}")
        return jsonify({"success": False, "msg": "验证码已过期，请刷新重试"}), 401

    # 获取学生姓名
    student_name = get_student_name(username)
    logging.info(f"📥 API登录尝试 - 学号: {username}, 姓名: {student_name}")

    # 尝试登录
    user_session = login_by_key(username, password, captcha_code, captcha_key)
    if not user_session:
        logging.warning(f"登录失败 - 学号: {username}, 姓名: {student_name}")
        return jsonify({"success": False, "msg": "登录失败"}), 401

    # 登录成功，保存session信息
    session["username"] = username
    session["student_name"] = student_name
    
    # 将cookies存入Redis，设置过期时间(例如1小时)
    rds.setex(
        f"user_session:{username}",
        3600,  # 1小时过期
        str(user_session.cookies.get_dict())
    )
    
    logging.info(f"✅ 登录成功 - 学号: {username}, 姓名: {student_name}")
    return jsonify({
        "success": True,
        "msg": "登录成功",
        "student_name": student_name
    })


@main.route("/api/grades")
def api_grades():
    # 检查用户是否登录
    if "username" not in session:
        grades_logger.warning("成绩查询失败: 用户未登录")
        return jsonify({"success": False, "msg": "未登录"}), 401
    
    username = session["username"]
    student_name = session.get("student_name", "未知姓名")
    
    # 从Redis获取session
    user_session = get_user_session(username)
    if not user_session:
        grades_logger.warning(f"成绩查询失败: 会话已过期 - 学号: {username}")
        return jsonify({"success": False, "msg": "会话已过期，请重新登录"}), 401

    # 获取查询参数
    kksj = request.args.get("kksj", "")
    kcxz = request.args.get("kcxz", "")
    kcmc = request.args.get("kcmc", "")
    xsfs = request.args.get("xsfs", "all")

    try:
        # 获取成绩数据
        grades_data = get_grades(user_session, kksj=kksj, kcxz=kcxz, kcmc=kcmc, xsfs=xsfs)
        
        # 记录日志
        grades_logger.info(
            f"✅ 成绩查询成功 - 学号: {username}, 姓名: {student_name}, "
            f"开课学期: '{kksj}', 课程性质: '{kcxz}', 课程名称关键词: '{kcmc}', "
            f"显示方式: '{xsfs}', 记录数: {len(grades_data)}"
        )

        return jsonify({
            "success": True,
            "data": {
                "sno": username,
                "sname": student_name,
                "grades": grades_data
            }
        })
    except Exception as e:
        grades_logger.error(f"成绩查询异常 - 学号: {username}, 错误: {str(e)}")
        return jsonify({"success": False, "msg": "获取成绩时发生错误"}), 500
    
    
@main.route("/api/aigrades")
def analyze_grades_auto():
    if "username" not in session:
        logging.warning("❌ AI分析失败：未登录用户访问")
        return jsonify({"success": False, "message": "未登录"}), 401

    username = session["username"]
    student_name = session.get("student_name", "未知姓名")
    logging.info(f"📥 开始AI分析请求 - 学号: {username}, 姓名: {student_name}")

    user_session = get_user_session(username)
    if not user_session:
        logging.warning(f"❌ AI分析失败：Redis会话不存在 - 学号: {username}")
        return jsonify({"success": False, "message": "会话已过期，请重新登录"}), 401

    kksj = request.args.get("kksj", "")
    kcxz = request.args.get("kcxz", "")
    kcmc = request.args.get("kcmc", "")
    xsfs = request.args.get("xsfs", "all")

    logging.info(f"📝 查询参数 - 学号: {username}, 学期: {kksj}, 课程性质: {kcxz}, 课程名称关键词: {kcmc}, 显示方式: {xsfs}")

    try:
        grades = get_grades(user_session, kksj, kcxz, kcmc, xsfs)
    except Exception as e:
        logging.error(f"❌ 获取成绩失败 - 学号: {username}, 错误: {str(e)}")
        return jsonify({"success": False, "message": "获取成绩数据失败"}), 500

    if not grades:
        logging.info(f"📭 成绩为空 - 学号: {username}")
        return jsonify({"success": False, "message": "没有找到成绩数据"}), 404

    logging.info(f"✅ 成绩获取成功 - 学号: {username}, 共 {len(grades)} 条记录")

    # 构建AI提示词
    log_text = f"分析一下{student_name}同学的成绩\n\n📋 查询到 {len(grades)} 条记录\n"
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
        logging.info(f"📡 正在发送分析请求至 AI 模型...")
        result = ask_ai(prompt)
        logging.info(f"✅ AI 分析完成 - 学号: {username}")
        return jsonify({
            "success": True,
            "sno": username,
            "sname": student_name,
            "analysis": result
        })
    except Exception as e:
        logging.error(f"❌ AI分析失败 - 学号: {username}, 错误: {str(e)}")
        return jsonify({"success": False, "message": f"分析失败: {str(e)}"}), 500


@main.route("/resources")
def show_resources():
    if "username" not in session:
        return redirect(url_for("main.login"))
    return render_template("resources.html",)

@main.route("/api/resources")
def api_resources():
    all_resources = get_all_resources()
    
    return jsonify({"data": all_resources})

@main.route("/download_resource")
def download_resource():
    if "username" not in session:
        return jsonify({"error": "未登录"}), 401

    resource_id = request.args.get("id", type=int)
    if not resource_id:
        return "参数错误", 400

    row = get_resource_by_id(resource_id)
    if not row:
        return abort(404, "资源不存在或已下架")

    filepath = row["path"]
    filename = os.path.basename(filepath)
    folder = os.path.dirname(filepath)

    username = session.get("username", "未知学号")
    student_name = session.get("student_name", "未知姓名")

    logging.info(f"📥 下载资源 - 学号: {username}, 姓名: {student_name}, 资源: {row['title']} ({filepath})")

    return send_from_directory(folder, filename, as_attachment=True, download_name=filename)


@main.route('/api/announcements')
def get_announcements():
    data = get_all_announcements()
    return jsonify({
        "code": 0,
        "message": "success",
        "data": data
    })


rds = redis.Redis(
    host='localhost',
    port=6379,
    username='binfinity',
    password='123456',
    decode_responses=True
)