import pymysql
import os
from config import DB_CONFIG, RESOURCE_BASE_DIR 

def get_db_connection():
    return pymysql.connect(
        **DB_CONFIG,
        cursorclass=pymysql.cursors.DictCursor
    )

# 定义一个函数，用于获取所有资源
def get_all_resources():
    # 获取数据库连接
    conn = get_db_connection()
    # 创建一个游标对象，用于执行SQL语句
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    # 执行SQL语句，从resources表中获取所有状态为1的资源，按照发布时间降序排列
    cursor.execute("""
        SELECT id, title, path, description, publish_time, author, view_count
        FROM resources WHERE status = 1 ORDER BY publish_time DESC
    """)
    # 获取所有查询结果
    data = cursor.fetchall()
    # 关闭游标
    cursor.close()
    # 关闭数据库连接
    conn.close()
    # 返回查询结果
    return data

def get_resource_by_id(resource_id):
    # 获取数据库连接
    conn = get_db_connection()
    # 创建游标
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    # 执行查询语句，获取指定id的资源
    cursor.execute("SELECT * FROM resources WHERE id = %s AND status = 1", (resource_id,))
    # 获取查询结果
    row = cursor.fetchone()
    # 如果查询结果不为空
    if row:
        # 执行更新语句，将资源的浏览次数加1
        cursor.execute("UPDATE resources SET view_count = view_count + 1 WHERE id = %s", (resource_id,))
        # 提交事务
        conn.commit()
    # 关闭游标
    cursor.close()
    # 关闭数据库连接
    conn.close()
    # 返回查询结果
    return row

# 定义一个添加资源的函数，参数为标题、路径、描述和作者
def add_resource(title, path, description=None, author=None):
    # 获取数据库连接
    conn = get_db_connection()
    # 创建游标
    cursor = conn.cursor()
    # 执行插入语句，将参数插入到resources表中
    cursor.execute("""
        INSERT INTO resources (title, path, description, publish_time, author)
        VALUES (%s, %s, %s, NOW(), %s)
    """, (title, path, description, author))
    # 提交事务
    conn.commit()
    # 关闭游标
    cursor.close()
    # 关闭数据库连接
    conn.close()
