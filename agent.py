"""
Agent 核心循环
实现了完整的"思考→行动→观察→再思考"的 Agent 决策循环
"""

import json
from openai import OpenAI
from config import get_config, SYSTEM_PROMPT, MAX_TURNS, TEMPERATURE
from tools import TOOL_DEFINITIONS, execute_tool


class Agent:
    """LLM Agent - 通过工具调用循环完成用户任务"""

    def __init__(self):
        cfg = get_config()
        self.client = OpenAI(
            base_url=cfg["base_url"],
            api_key=cfg["api_key"],
        )
        self.model = cfg["model"]
        self.messages = []

    def reset(self):
        """重置对话上下文"""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _call_llm(self) -> dict:
        """调用大模型，返回 API 响应消息"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=TOOL_DEFINITIONS,
            temperature=TEMPERATURE,
        )
        return response.choices[0].message

    def run(self, user_input: str) -> str:
        """
        执行一次用户请求，返回最终回复。
        核心流程：
          1. 将用户输入加入上下文
          2. 调用 LLM 获取响应
          3. 如果 LLM 返回工具调用 → 执行工具 → 结果加入上下文 → 回到步骤 2
          4. 如果 LLM 返回文本 → 任务完成，返回文本
        """
        self.messages.append({"role": "user", "content": user_input})

        for turn in range(MAX_TURNS):
            print(f"---第 {turn + 1} 轮---")
            msg = self._call_llm()

            # 情况 A: LLM 想调用工具
            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    print(f"\n  [Agent] 调用工具: {tool_name}({arguments})")

                    result, success = execute_tool(tool_name, arguments)
                    status = "OK" if success else "FAIL"
                    print(f"  [Agent] 结果 [{status}]: {result[:200]}")

                    # 将工具调用和结果加入对话历史
                    self.messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call],
                    })
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
                # 继续循环，让 LLM 看到工具结果后再次决策

            # 情况 B: LLM 返回纯文本，任务完成
            else:
                reply = msg.content or "(空回复)"
                self.messages.append({"role": "assistant", "content": reply})
                return reply

        return "已达到最大循环轮数，任务可能未完成。"

    def chat(self):
        """交互式对话循环"""
        self.reset()
        print("=" * 60)
        print("  AI Agent 编程助手")
        print(f"  模型: {self.model}")
        print("  输入 /reset 重置对话 | /exit 退出")
        print("=" * 60)

        while True:
            try:
                user_input = input("\n你> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break

            if not user_input:
                continue

            if user_input.lower() == "/exit":
                print("再见！")
                break

            if user_input.lower() == "/reset":
                self.reset()
                print("对话已重置。")
                continue

            print(f"\n  [Agent] 思考中...")
            reply = self.run(user_input)
            print(f"\nAgent> {reply}")
