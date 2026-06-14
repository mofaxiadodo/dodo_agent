"""
AI Agent 编程助手 - 入口文件

用法:
    python main.py              # 交互模式
    python main.py --task "..." # 单次任务模式

前置条件:
    1. 安装依赖: pip install -r requirements.txt
    2. 配置 API Key: 修改 config.py 或设置环境变量
       - DeepSeek: set DEEPSEEK_API_KEY=sk-xxx
       - OpenAI:   set OPENAI_API_KEY=sk-xxx
       - 千问:      set DASHSCOPE_API_KEY=sk-xxx
"""

import sys
import os

# Windows 终端默认 GBK，设置 UTF-8 避免中文乱码
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from agent import Agent


def main():
    agent = Agent()

    # 单次任务模式
    if len(sys.argv) >= 3 and sys.argv[1] == "--task":
        task = " ".join(sys.argv[2:])
        agent.reset()
        agent.messages.append({
            "role": "system",
            "content": "你是一个编程助手，回答应该简洁专业。",
        })
        print(f"任务: {task}\n")
        reply = agent.run(task)
        print(reply)
        return

    # 交互模式
    agent.chat()


if __name__ == "__main__":
    main()
