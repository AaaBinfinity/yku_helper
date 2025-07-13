# -*- coding: utf-8 -*-
import http.client
import json
import sys
import os
 
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(parent_dir)

from config import API_KEY, AI_MODEL_NAME, HOST, PATH

import logging

# 设置日志目录
log_dir = os.path.join(parent_dir, "app/log")
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录
log_file = os.path.join(log_dir, "askai.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()  # 控制台也显示
    ]
)


def ask_ai(prompt: str, api_key: str = API_KEY, model: str = AI_MODEL_NAME) -> str:
    # 将prompt转换为json格式
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": ""}
        ]
    })

    # 设置请求头
    headers = {
        'Authorization': f'Bearer {api_key}',
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Host': HOST,
        'Connection': 'keep-alive'
    }

    try:
        # 发送请求
        logging.info(f"···发送请求: {prompt}")
        conn = http.client.HTTPSConnection(HOST)
        conn.request("POST", PATH, payload, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()

        # 解码响应内容
        decoded = data.decode("utf-8")
        logging.info(f"····· 返回结果: {decoded}")

        # 将响应内容转换为json格式
        json_data = json.loads(decoded)
        # 获取响应内容
        content = json_data["choices"][0]["message"]["content"].strip()
        return content
    except Exception as e:
        # 记录错误日志
        logging.error(f"[ask_ai] ❌ 请求出错: {e}")
        # 记录响应内容
        logging.debug(f"响应内容: {data.decode('utf-8') if 'data' in locals() else '[无响应]'}")
        return "error"

# ask_ai("你好，AI助手！")  # 测试调用