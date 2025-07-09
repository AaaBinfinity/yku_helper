from dotenv import load_dotenv
import os

# ✅ 加载 .env 文件（必须调用）
load_dotenv()

class Config:
    SECRET_KEY = 'your-secret-key'

# AI 配置
API_KEY = os.getenv("API_KEY")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME")
HOST = "ark.cn-beijing.volces.com"
PATH = "/api/v3/chat/completions"
