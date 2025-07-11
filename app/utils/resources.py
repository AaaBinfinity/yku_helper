import pymysql
import os
from config import DB_CONFIG, RESOURCE_BASE_DIR  # 需要在config.py中添加RESOURCE_BASE_DIR配置

def get_db_connection():
    return pymysql.connect(
        **DB_CONFIG,
        cursorclass=pymysql.cursors.DictCursor
    )

def get_all_resources():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT id, title, path, description, publish_time, author, view_count
        FROM resources WHERE status = 1 ORDER BY publish_time DESC
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def get_resource_by_id(resource_id):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM resources WHERE id = %s AND status = 1", (resource_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE resources SET view_count = view_count + 1 WHERE id = %s", (resource_id,))
        conn.commit()
    cursor.close()
    conn.close()
    return row

def add_resource(title, path, description=None, author=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO resources (title, path, description, publish_time, author)
        VALUES (%s, %s, %s, NOW(), %s)
    """, (title, path, description, author))
    conn.commit()
    cursor.close()
    conn.close()
