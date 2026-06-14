"""
AI Agent 编程助手 - 入口文件

用法:
    python main.py              # 交互模式（可以跟 AI 聊天对话）
    python main.py --task "..." # 单次任务模式（一次性执行任务）

前置条件:
    1. 安装依赖: pip install -r requirements.txt
    2. 配置 API Key: 修改 config.py 或设置环境变量
       - DeepSeek: set DEEPSEEK_API_KEY=sk-xxx
       - OpenAI:   set OPENAI_API_KEY=sk-xxx
       - 千问:      set DASHSCOPE_API_KEY=sk-xxx
"""

import sys      # sys 模块：提供系统相关功能，比如读取命令行参数
import os       # os 模块：提供操作系统相关功能，比如环境变量

# Windows 终端默认用 GBK 编码，设置 UTF-8 可以避免中文乱码
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# 从 agent.py 文件中导入 Agent 类（Agent 是 AI 助手的核心）
from agent import Agent


def main():
    """程序的主函数，相当于 C 语言的 int main()"""

    # 创建一个 Agent 对象（相当于 C 里声明一个结构体变量并初始化）
    agent = Agent()

    # ============================================================
    # 模式一：单次任务模式
    # 判断条件：命令行参数 >= 3 个，且第一个参数是 "--task"
    # 例如：python main.py --task 帮我写个排序
    # ============================================================
    if len(sys.argv) >= 3 and sys.argv[1] == "--task":
        # sys.argv[2:] 表示从第2个参数开始取到末尾（列表切片）
        # " ".join(...) 用空格把列表里的元素拼成一个完整的字符串
        task = " ".join(sys.argv[2:])

        # 重置对话历史，清空之前的聊天记录
        agent.reset()

        # 往消息列表里添加一条"系统消息"，告诉 AI 它的身份和回答风格
        agent.messages.append({
            "role": "system",             # 消息角色：system（系统设定）
            "content": "你是一个编程助手，回答应该简洁专业。",  # 消息内容
        })

        # 打印任务内容，f-string 用 {} 插入变量的值
        print(f"任务: {task}\n")

        # 调用 agent.run() 执行任务，返回 AI 的回复
        reply = agent.run(task)

        # 打印 AI 的回复
        print(reply)

        # 退出 main 函数（相当于 C 的 return 0）
        return

    # ============================================================
    # 模式二：交互模式
    # 如果没有传 --task 参数，就进入聊天模式
    # ============================================================
    agent.chat()


# Python 特有的写法：判断当前文件是否被直接运行
# __name__ 是 Python 内置变量
#   - 直接运行 python main.py 时，__name__ 等于 "__main__"
#   - 被其他文件 import 时，__name__ 等于 "main"（不执行下面的代码）
if __name__ == "__main__":
    # 调用 main() 函数，程序从这里开始执行
    main()
