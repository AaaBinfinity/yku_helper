from flask_socketio import SocketIO, emit
from flask import session
from datetime import datetime
import logging
import pymysql
from config import DB_CONFIG

socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")  # 初始化SocketIO对象

def get_db_connection():
    return pymysql.connect(
        **DB_CONFIG,
        cursorclass=pymysql.cursors.DictCursor
    )

@socketio.on('connect')
def handle_connect():
    emit("system", {"msg": "✅ 已连接讨论服务器"})

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
        "content": content,
        "timestamp": now
    }, broadcast=True)
