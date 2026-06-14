"""
Agent 配置模块
支持多种模型提供商，可通过环境变量或直接修改此文件配置
"""

import os
from dotenv import load_dotenv
load_dotenv()

# ============================================================
# 模型配置 - 修改这里切换到不同提供商
# ============================================================

# 可选提供商: "deepseek" | "openai" | "qwen" | "zhipu" | "ollama"
PROVIDER = os.getenv("AGENT_PROVIDER", "deepseek")

# 各提供商的配置
PROVIDER_CONFIG = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "model": "deepseek-chat",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key": os.getenv("OPENAI_API_KEY", "your-openai-api-key"),
        "model": "gpt-4o",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": os.getenv("DASHSCOPE_API_KEY", "your-qwen-api-key"),
        "model": "qwen-plus",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "api_key": os.getenv("ZHIPU_API_KEY", "your-zhipu-api-key"),
        "model": "glm-4",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "model": "qwen2.5:7b",
    },
}

# ============================================================
# Agent 行为配置
# ============================================================

MAX_TURNS = 10           # 单次任务最大工具调用轮数
TEMPERATURE = 0.7        # 模型温度
SYSTEM_PROMPT = """\
你是一个编程助手 Agent，可以帮助用户完成编程任务。

你可以使用以下工具：
- read_file(path)    : 读取文件内容
- write_file(path, content): 写入文件
- run_command(cmd)   : 执行终端命令
- search_files(pattern, dir): 搜索匹配的文件

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
    """获取当前提供商的完整配置"""
    cfg = PROVIDER_CONFIG[PROVIDER]
    return {
        "base_url": cfg["base_url"],
        "api_key": cfg["api_key"],
        "model": cfg["model"],
    }
