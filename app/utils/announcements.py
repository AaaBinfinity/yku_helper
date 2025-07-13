import pymysql
from config import DB_CONFIG

# 定义一个函数，用于获取数据库连接
def get_db_connection():
    # 使用pymysql模块的connect函数，连接数据库
    return pymysql.connect(
        # 使用DB_CONFIG字典中的配置信息
        **DB_CONFIG,
        # 使用DictCursor类，将查询结果以字典形式返回
        cursorclass=pymysql.cursors.DictCursor
    )


def get_all_announcements():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, content, timestamp
        FROM announcements
        WHERE status = 1
        ORDER BY timestamp DESC
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def add_announcement(title, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO announcements (title, content, timestamp)
        VALUES (%s, %s, NOW())
    """, (title, content))
    conn.commit()
    cursor.close()
    conn.close()
