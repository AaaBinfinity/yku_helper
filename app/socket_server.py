from flask_socketio import SocketIO, emit
from flask import session
from datetime import datetime
import os
import logging
import pymysql
from config import DB_CONFIG  # 请确保你有这个配置文件

# === 日志配置 ===
log_dir = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(log_dir, exist_ok=True)

log_path = os.path.join(log_dir, "discussion.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# === 初始化 SocketIO ===
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")



# 数据库连接
def get_db_connection():
    return pymysql.connect(
        **DB_CONFIG,
        cursorclass=pymysql.cursors.DictCursor
    )

# 用户连接事件
@socketio.on('connect')
def handle_connect():
    emit("system", {"msg": "✅ 已连接讨论服务器"})

# 接收并广播消息
@socketio.on('send_message')
def handle_message(data):
    content = data.get("content", "").strip()
    if not content:
        return

    sno = session.get("username")
    name = session.get("student_name")

    if not sno or not name:
        emit("error", {"msg": "未登录用户无法发送消息"})
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO discussion_messages (sno, name, content, timestamp) VALUES (%s, %s, %s, %s)",
                (sno, name, content, now)
            )
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"[数据库写入失败] {name}({sno}): {e}")
        emit("error", {"msg": "服务器内部错误"})
        return

    logging.info(f"[匿名讨论] {name}({sno})：{content}")

    emit("new_message", {
        "sno": sno,  # 标记身份，前端用于区分“我”和“别人”
        "content": content,
        "timestamp": now
    }, broadcast=True)

# 加载最近历史消息
@socketio.on('request_history')
def handle_history():
    sno = session.get("username")
    if not sno:
        emit("error", {"msg": "未登录用户无法加载历史记录"})
        return

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT sno, name, content, timestamp FROM discussion_messages ORDER BY timestamp DESC LIMIT 100"
            )
            messages = cursor.fetchall()
        conn.close()
    except Exception as e:
        logging.error(f"[加载历史失败] {sno}: {e}")
        emit("error", {"msg": "加载历史消息失败"})
        return

    # 转换 timestamp 为字符串
    for msg in messages:
        if isinstance(msg["timestamp"], datetime):
            msg["timestamp"] = msg["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

    messages.reverse()
    emit("history", messages)
