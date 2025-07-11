import pymysql
# -*- coding: utf-8 -*-
import http.client
import json
import sys
import os

# 动态添加 config 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(parent_dir)

from config import API_KEY, AI_MODEL_NAME, HOST, PATH, DB_CONFIG

def get_connection():
    return pymysql.connect(
        **DB_CONFIG,
        cursorclass=pymysql.cursors.DictCursor
    )

def get_all_resources():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM resources ORDER BY publish_time DESC")
            resources = cursor.fetchall()
            for res in resources:
                cursor.execute("SELECT url FROM resource_links WHERE resource_id=%s", (res['id'],))
                res['links'] = [row['url'] for row in cursor.fetchall()]
            return {"success": True, "data": resources}
    finally:
        conn.close()
get_all_resources()