from dotenv import load_dotenv
import os

# 加载 .env 文件
load_dotenv()
# 数据库配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4"
}
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

# AI 配置
API_KEY = os.getenv("API_KEY")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME")
HOST = "ark.cn-beijing.volces.com"
PATH = "/api/v3/chat/completions"
 
 