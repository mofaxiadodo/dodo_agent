"""
my_agent.py — 最小 Agent，只有一个 calculator 工具
填写三处 TODO 就能跑
"""
import json
from openai import OpenAI
from config import get_config
import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")


# ============================================================
# TODO ①：工具定义（告诉 LLM 有这个工具）
# 照抄 tools.py 里 search_files 的格式，改 name/description/parameters
# ============================================================
TOOLS = [
    # 在这里填你的工具定义 JSON
    # 工具 1：读取文件
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式",
                    }
                },
                "required": ["expression"],  # expression 参数是必填的
            },
        },
    },
]


# ============================================================
# TODO ②：工具实现（真的会算数）
# 用 Python 的 eval() 计算表达式字符串，返回 (结果文本, 是否成功)
# 注意：eval 很危险，这里只是学习用
# ============================================================
def calculator(expression: str):
    # 在这里写：用 eval(expression) 计算，返回 (str(结果), True)
    # 如果 eval 报错，返回 ("计算出错: ...", False)
    try:
        result = eval(expression)
        return str(result), True
    except Exception as e:
        return f"计算出错: {e}", False


# 工具分发
TOOL_MAP = {"calculator": calculator}


def execute_tool(name, args):
    func = TOOL_MAP.get(name)
    if func is None:
        return f"未知工具: {name}", False
    try:
        return func(**args)
    except Exception as e:
        return f"执行失败: {e}", False


# ============================================================
# TODO ③：Agent 循环
# 仿照 agent.py 的 run() 方法写：
#   while True:
#       msg = LLM 调用
#       if msg.tool_calls → 执行工具 → 结果加入 messages → 继续
#       else → return msg.content
# ============================================================
def run_agent(user_input: str) -> str:
    cfg = get_config()
    client = OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    messages = [
        {"role": "system", "content": "你是一个数学助手，可以用 calculator 工具计算表达式。"},
        {"role": "user", "content": user_input},
    ]

    # 在这里写循环
    for _ in range(5):
        msg = client.chat.completions.create(
            model=cfg["model"],
            messages=messages,
            tools=TOOLS,
        )
        reply = msg.choices[0].message

        if reply.tool_calls:
            for tc in reply.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                result, ok = execute_tool(name, args)
                print(f"  [工具] {name}({args}) → {result}")
                messages.append({"role": "assistant", "tool_calls": [tc]})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        else:
            return reply.content or "(空)"

    return "达到最大轮数"


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    task = input("输入算式: ")
    print(run_agent(task))
