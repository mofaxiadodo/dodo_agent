"""
Agent 配置模块
支持多种模型提供商（DeepSeek、OpenAI、千问、智谱、Ollama）
可通过环境变量或直接修改此文件来配置
"""

import os                       # os 模块：读取环境变量
from dotenv import load_dotenv  # dotenv 库：从 .env 文件加载环境变量
load_dotenv()                   # 加载 .env 文件（如果有的话）

# ============================================================
# 模型配置 - 修改这里可以切换到不同的 AI 提供商
# ============================================================

# 当前使用的 AI 提供商名称
# 可选值: "deepseek" | "openai" | "qwen" | "zhipu" | "ollama"
# 优先读取环境变量 AGENT_PROVIDER，如果没设置则默认用 "deepseek"
PROVIDER = os.getenv("AGENT_PROVIDER", "deepseek")

# 各提供商的详细配置（字典嵌套）
# 每个提供商都有三个配置项：
#   - base_url: API 接口地址
#   - api_key:   API 密钥（从环境变量读取，保护敏感信息）
#   - model:     使用的模型名称
PROVIDER_CONFIG = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "api_key": os.getenv("DEEPSEEK_API_KEY"),          # 环境变量: DEEPSEEK_API_KEY
        "model": "deepseek-chat",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key": os.getenv("OPENAI_API_KEY", "your-openai-api-key"),  # 环境变量: OPENAI_API_KEY
        "model": "gpt-4o",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": os.getenv("DASHSCOPE_API_KEY", "your-qwen-api-key"), # 环境变量: DASHSCOPE_API_KEY
        "model": "qwen-plus",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "api_key": os.getenv("ZHIPU_API_KEY", "your-zhipu-api-key"),    # 环境变量: ZHIPU_API_KEY
        "model": "glm-4",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",  # Ollama 本地服务地址
        "api_key": "ollama",                       # 本地服务不需要密钥
        "model": "qwen2.5:7b",
    },
}

# ============================================================
# Agent 行为配置
# ============================================================

# 单次任务中，AI 最多可以调用多少次工具
# 防止 AI 陷入无限循环（比如反复读文件、反复执行命令）
MAX_TURNS = 10

# 模型温度参数（0.0 ~ 1.0）
# 值越低，回答越确定、越保守
# 值越高，回答越有创意、越随机
TEMPERATURE = 0.7

# 系统提示词：告诉 AI 它是什么身份、该怎么回答问题
# 这是每次对话开始时的"人设设定"
SYSTEM_PROMPT = """\
你是一个嗲声爹气的美少女，精通编程，以鼓励的方式指导用户。

你可以使用以下工具：
- read_file(path)    : 读取文件内容
- write_file(path, content): 写入文件
- run_command(cmd)   : 执行终端命令
- search_files(pattern, dir): 搜索匹配的文件
- list_dir(path)     : 列出目录下的文件和子目录

工作流程：
1. 理解用户的需求
2. 决定是否需要使用工具
3. 如果需要，选择最合适的工具
4. 根据工具结果决定下一步
5. 最终给出完整回答

注意：
- 一次只调用一个工具，除非多个工具互不依赖
- 写文件前先确认内容正确
- 执行命令时说明你在做什么
"""


def get_config():
    """
    获取当前选择的 AI 提供商的完整配置
    
    返回值: 一个字典，包含三个键：
        - "base_url": API 地址
        - "api_key":  API 密钥
        - "model":    模型名称
    
    使用示例：
        cfg = get_config()
        print(cfg["model"])  # 输出当前使用的模型名
    """
    # 从 PROVIDER_CONFIG 字典中，根据 PROVIDER 变量获取对应的配置
    cfg = PROVIDER_CONFIG[PROVIDER]
    
    # 返回配置字典
    return {
        "base_url": cfg["base_url"],
        "api_key": cfg["api_key"],
        "model": cfg["model"],
    }
